#! /usr/bin/env python
import os
import PIL
from PIL import Image
import click
from vertexai.generative_models import GenerativeModel
import google.generativeai as genai
from pathlib import Path
import sys
import logging
from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)
logging.getLogger("main")
logging.basicConfig(filename="LOG_FILE.log", encoding="utf-8", level=logging.INFO)

SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
DEFAULT_PROMPT = "Return the text present in this image."


def _prepare_model() -> GenerativeModel:
    """Create a gemini Generative Model"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("Missing 'GEMINI_API_KEY' environment variable.")
            raise EnvironmentError("Missing 'GEMINI_API_KEY' environment variable.")
        genai.configure(api_key=api_key)
    except Exception as err:
        logger.error("ERROR : %s", err)
        return None

    return genai.GenerativeModel("gemini-1.5-pro")


def get_image_text_from_gemini(model, image) -> str:
    """Get Gemini model & input image, return the text prsenst in the image"""
    # TODO Put this in try except for error handling
    try:
        result = model.generate_content([image, DEFAULT_PROMPT])
    except Exception as err:
        logging.error("ERROR : Gemini API Error \n %s ", err)
        sys.exit(1)
    return result.text


def get_all_directory(dirname: Path) -> list[Path]:
    """Get all the directory path for given directory"""
    try:
        subfolders = [folder.path for folder in os.scandir(dirname) if folder.is_dir()]
        for dirname in list(subfolders):
            subfolders.extend(get_all_directory(dirname))
    except Exception as err:
        logger.error("ERROR : %s", err)

    return subfolders


def get_image_files(directory: Path) -> list[__file__]:
    """Get all the images file present in the directory"""
    try:
        image_files = [
            path.name
            for path in Path(directory).iterdir()
            if path.suffix in SUPPORTED_IMAGE_EXTENSIONS
        ]
        return image_files
    except FileNotFoundError as err:
        logging.error("ERROR :  Error while retieving the image files \n %s", err)
        raise err


def get_image_text_file_name(image_file_name: __file__) -> str:
    """Get text file name, same as image file name with (dot) txt extension"""
    try:
        parts = image_file_name.split(".")
        text_file_name = parts[0] + ".txt"
        return text_file_name
    except ValueError as err:
        logging.error("ERROR : %s", err)
        raise ValueError()


def save_text_file(text: str, file_path: Path) -> None:
    """Save text file in the same path as it is for image"""
    try:
        with open(file_path, "w") as file:
            file.write(text)
    except IOError as err:
        logging.error("Error : %s", err)
        raise IOError
    
def exit_program():
    sys.exit(0)


@click.command()
@click.option(
    "--path",
    "-p",
    "paths",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True, path_type=Path),
    help="A path to a directory of images.....",
    multiple=True,
)
def cli(paths) -> None:
    """The function take image directory path &
    process to genrate text file in same directory path
    """

    model = _prepare_model()
    if model == None:
        logging.error("ERROR :  Generative model is not found ", )
        sys.exit("retrun 0")
    list_of_dir = []
   
    for dir_name in paths:
        list_of_dir = get_all_directory(dir_name)
    
    for directory_path in list_of_dir:
        image_files = get_image_files(directory_path)

        for image_file_name in image_files:
            text_file_name = get_image_text_file_name(image_file_name)
            image_file_path = Path(directory_path).joinpath(image_file_name)
            image_content = PIL.Image.open(image_file_path)
            # Get Image text via gemini
            text = get_image_text_from_gemini(model, image_content)
            # Write extracted text in corresponding text file
            text_file_path = Path(directory_path).joinpath(text_file_name)
            save_text_file(text, text_file_path)


if __name__ == "__main__":
    cli()
    exit_program()