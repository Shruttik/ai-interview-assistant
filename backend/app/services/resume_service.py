import os
import PyPDF2
from backend.app.utils.logger import logger

class ResumeService:
    """
    Service responsible for reading and extracting plain text from uploaded resume documents.
    Supports PDF and plain text formats.
    """

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Parses a PDF file and extracts text contents page by page.
        """
        text = ""
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += extracted_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            raise ValueError(f"Could not parse PDF file: {e}")

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """
        Reads a standard text file.
        """
        try:
            logger.info(f"Extracting text from TXT: {file_path}")
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Failed to extract text from TXT {file_path}: {e}")
            raise ValueError(f"Could not parse text file: {e}")

    def extract_text(self, file_path: str) -> str:
        """
        Main entry point for resume extraction.
        Automatically detects file extension and routes to correct parser.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")
            
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_extension in [".txt", ".md"]:
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file type uploaded: {file_extension}")
            raise ValueError(f"Unsupported file format '{file_extension}'. Please upload a PDF or TXT file.")

# Single instance of ResumeService to be imported
resume_service = ResumeService()
