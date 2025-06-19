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
import re
import subprocess
import sys
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
    INTERIM_DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
)
from src.mwplu.post_data import process_all_json_files, process_json_file


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
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(f"Error loading {yaml_file}: {e}")

        return configs

    @abstractmethod
    def generate_tasks(self) -> List[ProcessingTask]:
        """Generate a list of processing tasks."""
        pass  # pylint: disable=unnecessary-pass

    @abstractmethod
    def execute_task(self, task: ProcessingTask) -> bool:
        """Execute a single task. Returns True if successful."""
        pass  # pylint: disable=unnecessary-pass


class MainPipelineProcessor(BaseProcessor):
    """Processor for main.py pipeline commands (OCR, extract_pages, synthesis)."""

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

    def execute_task(self, task: ProcessingTask):
        """Execute a single main.py task."""
        # Quick check to avoid subprocess overhead for already-completed tasks
        cmd = ["python", str(self.main_py)]

        # Add stage command first
        cmd.append(task.stage.value)

        # Add common arguments
        if task.city:
            cmd.extend(["--name-city", task.city])
        if task.document:
            cmd.extend(["--name-document", task.document])

        # Add stage-specific arguments
        if task.stage == PipelineStage.OCR:
            if task.zoning:
                cmd.extend(["--name-zoning", task.zoning])
            if task.date_creation:
                cmd.extend(["--date-creation-source-document", task.date_creation])
        elif task.stage == PipelineStage.SYNTHESIS:
            if task.zoning:
                cmd.extend(["--name-zoning", task.zoning])
            if "dispositions_generales" in task.extra_params:
                cmd.extend(
                    [
                        "--dispositions-generales",
                        task.extra_params["dispositions_generales"],
                    ]
                )

        if self._should_skip_task(task):
            logger.debug(f"Skipping {' '.join(cmd)} - output already exists")
            return

        logger.trace(f"Executing: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # Display the actual error from the subprocess without showing our traceback
            logger.error(f"Command failed: {' '.join(e.cmd)}")
            logger.error(f"Exit code: {e.returncode}")

            if e.stdout and e.stdout.strip():
                logger.error(f"Stdout:\n{e.stdout}")

            if e.stderr and e.stderr.strip():
                logger.error(f"Error details:\n{e.stderr}")

            # Re-raise without showing our own traceback stack
            sys.exit(1)

    def _should_skip_task(self, task: ProcessingTask) -> bool:
        """Check if a task should be skipped because output already exists."""
        if task.stage == PipelineStage.SYNTHESIS:
            # Check if synthesis output already exists
            if task.city and task.zoning and task.document:
                output_path = (
                    PROCESSED_DATA_DIR
                    / task.city
                    / task.zoning
                    / f"{task.document}.json"
                )
                return output_path.exists()

        elif task.stage == PipelineStage.OCR:
            # Check if OCR output already exists
            if task.city and task.zoning and task.document:
                output_path = (
                    RAW_DATA_DIR / task.city / task.zoning / f"{task.document}.json"
                )
                return output_path.exists()

        elif task.stage == PipelineStage.EXTRACT_PAGES:
            # Check if extract_pages output already exists
            if task.city and task.document:
                output_path = (
                    INTERIM_DATA_DIR
                    / task.city
                    / task.document
                    / f"{task.document}.json"
                )
                return output_path.exists()

        return False

    def _is_date_format(self, date_str: str) -> bool:
        """Check if a string matches the YYYY-MM-DD format."""
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

    def execute_task(self, task: ProcessingTask):
        """Execute a single Supabase upload task."""
        if not self.supabase:
            logger.error("Supabase client not initialized. Cannot execute task.")
            return

        if task.city == "all":
            logger.info("Uploading all processed files to Supabase...")
            process_all_json_files(self.supabase)
        else:
            # Construct the path safely
            path_parts = [task.city]
            if task.zoning:
                path_parts.append(task.zoning)
            if task.document:
                path_parts.append(f"{task.document}.json")

            file_path = PROCESSED_DATA_DIR.joinpath(*path_parts)

            if file_path.exists():
                logger.info(f"Uploading {file_path} to Supabase...")
                process_json_file(self.supabase, file_path)
            else:
                logger.warning(f"File not found, skipping upload: {file_path}")


class BulkProcessor:
    """Orchestrates the bulk processing pipeline."""

    def __init__(self, config_dir: Path = CONFIG_DIR):
        self.config_dir = config_dir
        self.main_processor = MainPipelineProcessor(config_dir)
        self.supabase_processor = SupabaseProcessor(config_dir=config_dir)

    def run_pipeline_stages(
        self,
        stages: List[PipelineStage],
        cities: Optional[List[str]] = None,
        dry_run: bool = False,
        limit: Optional[int] = None,
    ):
        """
        Run the specified pipeline stages for the given cities.

        Args:
            stages: List of pipeline stages to run
            cities: List of cities to process (None for all)
            dry_run: If True, show what would be executed without running
            limit: Maximum number of tasks to execute (None for all tasks)
        """
        all_cities = self.get_available_cities()
        target_cities = all_cities if not cities or "all" in cities else set(cities)

        main_processor = MainPipelineProcessor(self.config_dir)
        supabase_processor = SupabaseProcessor(config_dir=self.config_dir)

        # Generate all possible tasks
        all_main_tasks = main_processor.generate_tasks(stages)
        all_supabase_tasks = supabase_processor.generate_tasks()

        # Filter tasks by city
        tasks_to_run = [
            task
            for task in all_main_tasks
            if task.city in target_cities and task.stage in stages
        ]

        if PipelineStage.UPLOAD_SUPABASE in stages:
            tasks_to_run.extend(
                [
                    task
                    for task in all_supabase_tasks
                    if task.city in target_cities
                    or (task.city == "all" and (not cities or "all" in cities))
                ]
            )

        # Apply limit if specified
        if limit is not None and limit > 0:
            tasks_to_run = tasks_to_run[:limit]

        if dry_run:
            logger.info("[DRY RUN] The following tasks would be executed:")
            for task in tasks_to_run:
                logger.info(
                    f"  - Stage: {task.stage.value}, City: {task.city}, "
                    f"Zoning: {task.zoning}, Document: {task.document}"
                )
            logger.info(f"Total tasks: {len(tasks_to_run)}")
            return

        logger.info(f"Starting bulk processing for {len(tasks_to_run)} tasks...")

        for i, task in enumerate(tasks_to_run):
            print("\n")
            logger.info(f"Executing task {i + 1}/{len(tasks_to_run)}")
            if task.stage == PipelineStage.UPLOAD_SUPABASE:
                supabase_processor.execute_task(task)
            else:
                main_processor.execute_task(task)

        logger.info("Bulk processing finished.")

    def get_available_cities(self) -> Set[str]:
        """Get a set of all available cities from the external config."""
        cities = set()

        for config_data in self.main_processor.yaml_configs.values():
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
