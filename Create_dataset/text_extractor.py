import pdfplumber
import os
from pathlib import Path

def pdf_to_txt(input_pdf_path, output_txt_path):
    """
    Extract text from a PDF and save as a TXT file
    """
    try:
        with pdfplumber.open(input_pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                # Extract text from page
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"  # Add spacing between pages
            
            # Save to TXT file
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        print(f"Successfully converted: {input_pdf_path} -> {output_txt_path}")
    
    except Exception as e:
        print(f"Error processing {input_pdf_path}: {str(e)}")

def batch_pdf_to_txt(input_dir, output_dir):
    """
    Convert all PDFs in a directory to TXT files
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in input_dir.glob("*.pdf"):
        txt_file = output_dir / f"{pdf_file.stem}.txt"
        pdf_to_txt(pdf_file, txt_file)

if __name__ == "__main__":
    # Set your input/output directories
    PDF_DIR = "C:/Users/JUAN MIKE/Desktop/Bob-the-lawyer/Bob-the-lawyer/Laws/Conventions"  # Folder containing your PDFs
    TXT_DIR = "C:/Users/JUAN MIKE/Desktop/Bob-the-lawyer/Bob-the-lawyer/Create_dataset/ConventionsTXT" # Folder to save TXT files
    
    # Convert all PDFs in directory
    batch_pdf_to_txt(PDF_DIR, TXT_DIR)