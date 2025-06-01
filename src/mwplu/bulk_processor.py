#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bulk Processor Module
This module provides a comprehensive bulk processing system for PLU data.
It leverages YAML configuration files to orchestrate different pipeline stages.

Version: 1.0
Date: 2025-05-28
Author: Grey Panda
"""

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from loguru import logger
from supabase import Client, create_client

from src.config import (
    CONFIG_DIR,
    PROCESSED_DATA_DIR,
)
from src.mwplu.post_data import process_all_json_files, process_json_file
from src.utils.plu import get_source_plu_url


class PipelineStage(Enum):
    """Enumeration of available pipeline stages."""

    OCR = "ocr"
    EXTRACT_PAGES = "extract_pages"
    SYNTHESIS = "synthesis"
    UPLOAD_SUPABASE = "upload_supabase"


@dataclass
class ProcessingTask:
    """Represents a single processing task."""

    stage: PipelineStage
    city: str
    zoning: Optional[str] = None
    document: Optional[str] = None
    date_creation: Optional[str] = None
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class BaseProcessor(ABC):
    """Abstract base class for processors."""

    def __init__(self, config_dir: Path = CONFIG_DIR):
        self.config_dir = config_dir
        self.yaml_configs = self._load_yaml_configs()

    def _load_yaml_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load all YAML configuration files."""
        configs = {}
        plu_config_dir = self.config_dir / "plu"

        for yaml_file in plu_config_dir.glob("plu_*.yaml"):
            config_name = yaml_file.stem  # e.g., "plu_processed" -> "plu_processed"
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    configs[config_name] = yaml.safe_load(f)
                logger.debug(f"Loaded config: {config_name}")
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")

        return configs

    @abstractmethod
    def generate_tasks(self) -> List[ProcessingTask]:
        """Generate a list of processing tasks."""
        pass

    @abstractmethod
    def execute_task(self, task: ProcessingTask) -> bool:
        """Execute a single task. Returns True if successful."""
        pass


class MainPipelineProcessor(BaseProcessor):
    """Processor for main.py pipeline commands (OCR, extract_pages, synthesis, reports)."""

    def __init__(self, config_dir: Path = CONFIG_DIR):
        super().__init__(config_dir)
        self.main_py = Path("main.py")

    def generate_tasks_from_external(
        self, stages: List[PipelineStage]
    ) -> List[ProcessingTask]:
        """Generate tasks from external data structure."""
        tasks = []
        external_config = self.yaml_configs.get("plu_external", {}).get("data", {})

        for city, city_data in external_config.items():
            if city_data.get("type") != "directory":
                continue

            city_contents = city_data.get("contents", {})

            # Handle different structures
            for date_or_zoning, content in city_contents.items():
                if content.get("type") != "directory":
                    continue

                # Check if this is a date-based structure (like bordeaux)
                if self._is_date_format(date_or_zoning):
                    # Date-based structure: city/date/zoning/documents
                    date_creation = date_or_zoning
                    for zoning, zoning_data in content.get("contents", {}).items():
                        if zoning_data.get("type") != "directory":
                            continue
                        for doc_name, doc_data in zoning_data.get(
                            "contents", {}
                        ).items():
                            if doc_data.get("type") == "file" and doc_name.endswith(
                                ".pdf"
                            ):
                                document = doc_name.replace(".pdf", "")
                                if PipelineStage.OCR in stages:
                                    tasks.append(
                                        ProcessingTask(
                                            stage=PipelineStage.OCR,
                                            city=city,
                                            zoning=zoning,
                                            document=document,
                                            date_creation=date_creation,
                                        )
                                    )
                else:
                    # Direct structure: city/documents (like nantes, grenoble)
                    for doc_name, doc_data in content.get("contents", {}).items():
                        if doc_data.get("type") == "file" and doc_name.endswith(".pdf"):
                            document = doc_name.replace(".pdf", "")
                            if PipelineStage.OCR in stages:
                                tasks.append(
                                    ProcessingTask(
                                        stage=PipelineStage.OCR,
                                        city=city,
                                        document=document,
                                        date_creation="2024-01-01",  # Default date
                                    )
                                )

        return tasks

    def generate_tasks_from_interim(
        self, stages: List[PipelineStage]
    ) -> List[ProcessingTask]:
        """Generate synthesis tasks from interim data structure."""
        tasks = []
        interim_config = self.yaml_configs.get("plu_interim", {}).get("data", {})

        for city, city_data in interim_config.items():
            if city_data.get("type") != "directory":
                continue

            city_contents = city_data.get("contents", {})
            dispositions_generales = None

            # Find dispositions générales for this city
            if "Dispositions Générales" in city_contents:
                dispositions_generales = "Dispositions Générales"

            for zoning, zoning_data in city_contents.items():
                if zoning_data.get("type") != "directory" or zoning in [
                    "Dispositions Générales",
                    "Règles Applicables au Patrimoine",
                ]:
                    continue

                for doc_name, doc_data in zoning_data.get("contents", {}).items():
                    if doc_data.get("type") == "file" and doc_name.endswith(".json"):
                        document = doc_name.replace(".json", "")

                        if PipelineStage.SYNTHESIS in stages:
                            extra_params = {}
                            if dispositions_generales:
                                extra_params["dispositions_generales"] = (
                                    dispositions_generales
                                )

                            tasks.append(
                                ProcessingTask(
                                    stage=PipelineStage.SYNTHESIS,
                                    city=city,
                                    zoning=zoning,
                                    document=document,
                                    extra_params=extra_params,
                                )
                            )

        return tasks

    def generate_tasks_from_raw(
        self, stages: List[PipelineStage]
    ) -> List[ProcessingTask]:
        """Generate extract_pages tasks from raw data structure."""
        tasks = []
        raw_config = self.yaml_configs.get("plu_raw", {}).get("data", {})

        for city, city_data in raw_config.items():
            if city_data.get("type") != "directory":
                continue

            city_contents = city_data.get("contents", {})

            for doc_name, doc_data in city_contents.items():
                if doc_data.get("type") == "file" and doc_name.endswith(".json"):
                    document = doc_name.replace(".json", "")

                    if PipelineStage.EXTRACT_PAGES in stages:
                        tasks.append(
                            ProcessingTask(
                                stage=PipelineStage.EXTRACT_PAGES,
                                city=city,
                                document=document,
                            )
                        )

        return tasks

    def generate_tasks(
        self, stages: List[PipelineStage] = None
    ) -> List[ProcessingTask]:
        """Generate tasks based on YAML configurations."""
        if stages is None:
            stages = list(PipelineStage)

        tasks = []

        # Generate tasks based on stages requested
        if any(stage in stages for stage in [PipelineStage.OCR]):
            tasks.extend(self.generate_tasks_from_external(stages))

        if any(stage in stages for stage in [PipelineStage.EXTRACT_PAGES]):
            tasks.extend(self.generate_tasks_from_raw(stages))

        if any(stage in stages for stage in [PipelineStage.SYNTHESIS]):
            tasks.extend(self.generate_tasks_from_interim(stages))

        return tasks

    def execute_task(self, task: ProcessingTask) -> bool:
        """Execute a main.py pipeline task."""
        try:
            cmd = ["python", str(self.main_py), task.stage.value]

            # Add city parameter
            cmd.extend(["--name-city", task.city])

            # Add stage-specific parameters
            if task.stage == PipelineStage.OCR:
                if task.date_creation:
                    cmd.extend(["--date-creation-source-document", task.date_creation])
                if task.zoning and task.zoning != "None":
                    cmd.extend(["--name-zoning", task.zoning])
                if task.document:
                    cmd.extend(["--name-document", task.document])

            elif task.stage in [PipelineStage.EXTRACT_PAGES]:
                if task.document:
                    cmd.extend(["--name-document", task.document])

            elif task.stage in [PipelineStage.SYNTHESIS]:
                if task.zoning:
                    cmd.extend(["--name-zoning", task.zoning])
                if task.document:
                    cmd.extend(["--name-document", task.document])

                if task.stage == PipelineStage.SYNTHESIS:
                    dg = task.extra_params.get("dispositions_generales", "None")
                    cmd.extend(["--dispositions-generales", dg])

            elif task.stage == PipelineStage.UPLOAD_SUPABASE:
                # For upload_supabase, we need city, zoning, and document parameters
                if task.zoning:
                    cmd.extend(["--name-zoning", task.zoning])
                if task.document:
                    cmd.extend(["--name-document", task.document])

            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.success(f"Task completed: {task.stage.value} for {task.city}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Task failed: {task.stage.value} for {task.city}")
            logger.error(f"Command: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error in task {task.stage.value} for {task.city}: {e}"
            )
            return False

    def _is_date_format(self, date_str: str) -> bool:
        """Check if string matches date format YYYY-MM-DD."""
        import re

        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))


class SupabaseProcessor(BaseProcessor):
    """Processor for uploading data to Supabase."""

    def __init__(
        self, supabase_client: Optional[Client] = None, config_dir: Path = CONFIG_DIR
    ):
        super().__init__(config_dir)
        self.supabase = supabase_client or self._create_supabase_client()

    def _create_supabase_client(self) -> Optional[Client]:
        """Create Supabase client from environment variables."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            logger.error(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
            )
            return None

        return create_client(url, key)

    def generate_tasks(self) -> List[ProcessingTask]:
        """Generate Supabase upload tasks from processed data."""
        tasks = []
        processed_config = self.yaml_configs.get("plu_processed", {}).get("data", {})

        for city, city_data in processed_config.items():
            if city_data.get("type") != "directory":
                continue

            # Add a single task to process all JSON files for this city
            tasks.append(ProcessingTask(stage=PipelineStage.UPLOAD_SUPABASE, city=city))

        return tasks

    def execute_task(self, task: ProcessingTask) -> bool:
        """Execute Supabase upload task."""
        if not self.supabase:
            logger.error("Supabase client not available")
            return False

        try:
            if task.city == "all":
                # Process all JSON files
                process_all_json_files(self.supabase, get_source_plu_url)
            else:
                # Process specific city files
                city_dir = PROCESSED_DATA_DIR / task.city
                json_files = list(city_dir.glob("**/*.json"))

                success_count = 0
                for json_file in json_files:
                    try:
                        result = process_json_file(
                            self.supabase, json_file, get_source_plu_url
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error uploading {json_file}: {e}")

                logger.info(
                    f"Uploaded {success_count}/{len(json_files)} files for {task.city}"
                )

            return True

        except Exception as e:
            logger.error(f"Error in Supabase upload task for {task.city}: {e}")
            return False


class BulkProcessor:
    """Main bulk processor that orchestrates different processors."""

    def __init__(self, config_dir: Path = CONFIG_DIR):
        self.config_dir = config_dir
        self.main_processor = MainPipelineProcessor(config_dir)
        self.supabase_processor = SupabaseProcessor(config_dir=config_dir)

    def run_pipeline_stages(
        self,
        stages: List[PipelineStage],
        cities: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Run specific pipeline stages for selected cities."""

        # Generate tasks
        if PipelineStage.UPLOAD_SUPABASE in stages:
            supabase_tasks = self.supabase_processor.generate_tasks()
            if cities:
                supabase_tasks = [
                    t for t in supabase_tasks if t.city in cities or "all" in cities
                ]
        else:
            supabase_tasks = []

        main_tasks = self.main_processor.generate_tasks(stages)
        if cities:
            main_tasks = [t for t in main_tasks if t.city in cities]

        all_tasks = main_tasks + supabase_tasks

        if dry_run:
            logger.info(f"DRY RUN: Would execute {len(all_tasks)} tasks:")
            for task in all_tasks:
                logger.info(
                    f"  - {task.stage.value}: {task.city} / {task.zoning} / {task.document}"
                )
            return {"total_tasks": len(all_tasks), "tasks": all_tasks}

        # Execute tasks
        results = {"successful": 0, "failed": 0, "total": len(all_tasks)}

        for i, task in enumerate(all_tasks, 1):
            logger.info(f"Processing task {i}/{len(all_tasks)}: {task.stage.value}")

            if task.stage == PipelineStage.UPLOAD_SUPABASE:
                success = self.supabase_processor.execute_task(task)
            else:
                success = self.main_processor.execute_task(task)

            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1

        return results

    def get_available_cities(self) -> Set[str]:
        """Get list of available cities from all configurations."""
        cities = set()

        for config_name, config_data in self.main_processor.yaml_configs.items():
            data = config_data.get("data", {})
            cities.update(data.keys())

        return cities

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of data across different pipeline stages."""
        status = {}

        for config_name, config_data in self.main_processor.yaml_configs.items():
            stage = config_name.replace("plu_", "")
            data = config_data.get("data", {})

            stage_status = {}
            for city, city_data in data.items():
                if city_data.get("type") == "directory":
                    file_count = self._count_files_recursive(
                        city_data.get("contents", {})
                    )
                    stage_status[city] = file_count

            status[stage] = stage_status

        return status

    def _count_files_recursive(self, contents: Dict[str, Any]) -> int:
        """Recursively count files in a directory structure."""
        count = 0
        for item_data in contents.values():
            if item_data.get("type") == "file":
                count += 1
            elif item_data.get("type") == "directory":
                count += self._count_files_recursive(item_data.get("contents", {}))
        return count
