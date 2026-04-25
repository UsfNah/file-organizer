"""Organises files in subfolders based on extension; config driven; safe dry-run mode"""
import argparse
import json
import logging
import shutil
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
DEFAULT_CONFIG = {
            "source": "./",
            "destination": "./organized",
            "extensions": {
                ".pdf": "Documents",
                ".docx": "Documents",
                ".txt": "Documents",
                ".jpg": "Images",
                ".jpeg": "Images",
                ".png": "Images",
                ".gif": "Images",
                ".mp4": "Videos",
                ".mkv": "Videos",
                ".mp3": "Audio",
                ".wav": "Audio",
                ".zip": "Archives",
                ".rar": "Archives",
                ".py": "Code",
                ".cpp": "Code",
                ".ipynb": "Code"
            },
            "others_folder": "Misc",
            "recursive": False
        }



def parse_args():
    """Returns parsed name space without side effects"""
    parser = argparse.ArgumentParser(description="Organize files into folders based on extension")
    parser.add_argument(
        "-s","--source",default=None
        ,type=str, help="path string"
    )
    parser.add_argument("-c","--config",default="config.json"
        ,type=str, help="path to the config file"
    )
    parser.add_argument("-n","--dry_run", action="store_true"
        , help="defines whether to dry run the program"
    )
    parser.add_argument("-v","--verbose",action="store_true",help=(
            "Print per-file details to the console (skipped files, "
            "duplicate resolutions, destination mappings). "
            "By default, only summaries and errors are shown."
        ))
    parser.add_argument("-l","--log_level",type=str,metavar="LEVEL",
            choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"]
            ,default="INFO",help=(
            "Set the logging verbosity level for organizer.log and console output. "
            "Choices: DEBUG (all internal details), INFO (default, moves and summaries), "
            "WARNING (anomalies only), ERROR (failures only), CRITICAL (fatal errors only). "
            "Default: INFO"
        ))
    return parser.parse_args()

def validate_config_dict(config_dict: dict):
    """validates a config dict to ensure that it has no errors"""
    if (("source" not in config_dict)
        or (not isinstance(config_dict["source"],str))
        or (config_dict.get("source") == "")):
        raise ValueError("Missing or invalid source in config")
    if (("destination" not in config_dict)
        or (not isinstance(config_dict["destination"],str))
        or (config_dict.get("destination") == "")):
        raise ValueError("Missing or invalid destination in config")


    if "extensions" not in config_dict:
        raise ValueError("Missing or invalid extensions")

    if not isinstance(config_dict["extensions"],dict):
        raise ValueError("Extensions should be dict")

    for key in config_dict["extensions"]:
        if not isinstance(key,str):
            raise ValueError("Extensions should be non empty strings")
        if key == "":
            raise ValueError("Extensions should be non empty strings")
        if not key.startswith("."):
            raise ValueError("Invalid extension")
        if key.lower() != key:
            raise ValueError("Invalid extension")


    if (("others_folder" not in config_dict)
        or (not isinstance(config_dict["others_folder"],str))
        or (config_dict.get("others_folder") == "")):
        raise ValueError("Missing or invalid others_folder in config")

    if "recursive" not in config_dict:
        config_dict["recursive"] =  DEFAULT_CONFIG["recursive"]
    elif not isinstance(config_dict["recursive"],bool):
        raise ValueError("Invalid recursive type")

def load_config(config_path : Path):
    """Returns a normalized config dict that has all config settings"""

    if config_path.exists():
        if not config_path.is_file():
            raise ValueError("Config file is not a valid file")

        try:
            config = config_path.read_text(encoding="utf-8")
            if config.strip() == "":
                raise ValueError("Empty config file")
            config_dict = json.loads(config)
        except json.JSONDecodeError as e:
            raise ValueError(f" Invalid JSON in {config_path}:"
            f"   Line {e.lineno}, Col {e.colno}: {e.msg}") from e
        validate_config_dict(config_dict)
        return config_dict
    config_path.parent.mkdir(parents=True,exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG,f, indent=2)
    return DEFAULT_CONFIG

def setup_logging(log_file : Path, level : str):
    """Creates a logger that logs to log_file and sets its level to level"""
    logger = logging.getLogger("file_organizer")

    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level,int):
        numeric_level = logging.INFO
    logger.setLevel(numeric_level)

    if not logger.handlers:
        file_handler = RotatingFileHandler(str(log_file),maxBytes=5*1024*1024,backupCount=3)
        stream_handler = logging.StreamHandler()

        handler_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(handler_formatter)
        stream_handler.setFormatter(handler_formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

def get_destination(ext:str, config: dict):
    """Takes a extension and searches for the coresponding file name in the dict
    otherwise searches for the others_folder file name and return a Path"""
    ext = ext.lower()
    folder_name = config["extensions"].get(ext,config["others_folder"])
    return Path(config["destination"])/folder_name

def handle_duplicates(dest_path: Path,logger: logging.Logger) -> Path:
    """Takes a file path and check if it is a duplicate if its not returns the 
    same file path else tries to resolve the duplicate if it 
    fails it logs a warning and returns same file path"""

    if not dest_path.exists():
        return dest_path

    parent = dest_path.parent
    stem = dest_path.stem
    suffix = dest_path.suffix
    for i in range(2,101):
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            logger.debug(f"Resolved duplicate: {dest_path} -> {candidate}")
            return candidate
    logger.warning(f"Too many duplicates for {dest_path}")
    return dest_path

def move_file(src: Path, dest :Path, dry_run: bool, logger: logging.Logger) -> bool:
    """moves files and creates logs"""
    if dry_run:
        logger.info(f"[DRY-RUN] Would move: {src} -> {dest}")
        return True

    dest.parent.mkdir(parents=True,exist_ok=True)
    new_dest = handle_duplicates(dest,logger)
    if new_dest.exists():
        logger.error()
        return False
    dest = new_dest
    try:
        shutil.move(str(src),str(dest))
        logger.info(f"Moved: {src} -> {dest}")
        return True
    except PermissionError:
        logger.error(f"Permission denied moving {src} -> {dest}")
        return False
    except OSError as e:
        logger.error(f"OS error moving {src} -> {dest}: {e}")
        return False


def organize_folder(
    src: Path, config: dict, dry_run:
    bool, logger: logging.Logger) -> tuple[int, int ,list]:
    """Organizes a folder that is at src based on config and returns
    how many files were found and how many were moved and error list"""
    if not src.exists():
        raise FileNotFoundError(f"{src} does not exist")
    if not src.is_dir():
        raise NotADirectoryError
    errors = []
    processed_count = 0
    moved_count = 0
    for i in src.iterdir():
        if not i.is_dir():
            processed_count += 1
            ext = i.suffix.lower()

            dest_dir = get_destination(ext,config)
            dest_path = dest_dir / i.name

            success = move_file(i,dest_path,dry_run,logger)
            if success:
                moved_count += 1
            else:
                errors.append((i , "See log for details"))

    return (processed_count,moved_count,errors)


def main() ->int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    try:
        config = load_config(config_path)
    except ValueError as e:
        print(f"Error occured {e}", file = sys.stderr)
        return 1
    if args.source is not None:
        src_dir = Path(args.source).expanduser().resolve()
    else:
        src_dir = Path(config["source"]).expanduser().resolve()
    log_file = Path("Organizer.log").resolve()
    logger = setup_logging(log_file,args.log_level)
    logger.info("source: %s, destination: %s ,dry_run: %s, log_level: %s"
    ,src_dir,config["destination"],args.dry_run,args.log_level)

    try:
        processed, move, errors = organize_folder(src_dir,config,args.dry_run,logger)
    except (FileNotFoundError,NotADirectoryError):
        logger.critical()
        return 1
    except Exception:
        logger.exception(...)
        return 2
    logger.info("Processed: %s files, Moved: %s , Errors: %s",processed,move,len(errors))
    return 0

main()
