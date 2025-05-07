import pdfplumber
from pathlib import Path

def pdf_to_text(input_pdf_path):
    """
    Extract text from a PDF and return as string
    """
    try:
        with pdfplumber.open(input_pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                # Extract text from page
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"  # Add spacing between pages
            return text
    
    except Exception as e:
        print(f"Error processing {input_pdf_path}: {str(e)}")
        return None

def batch_pdf_to_single_txt(input_dir, output_file_path):
    """
    Convert all PDFs in a directory to a single TXT file
    """
    input_dir = Path(input_dir)
    output_file_path = Path(output_file_path)
    
    # Create parent directory if it doesn't exist
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        for pdf_file in input_dir.glob("*.pdf"):
            print(f"Processing: {pdf_file.name}")
            pdf_text = pdf_to_text(pdf_file)
            if pdf_text:
                # Add separator with PDF filename
                output_file.write(f"\n\n=== {pdf_file.name} ===\n\n")
                output_file.write(pdf_text)
    
    print(f"All PDFs combined and saved to: {output_file_path}")

if __name__ == "__main__":
    # Set your input/output paths
    PDF_DIR = r"C:\Users\JUAN MIKE\Desktop\Bob-the-lawyer\Bob-the-lawyer\LOIS_LAWS"
    OUTPUT_TXT = "C:/Users/JUAN MIKE/Desktop/Bob-the-lawyer/Bob-the-lawyer/Create_dataset/CameroonLaw.txt"
    
    # Convert all PDFs to a single TXT file
    batch_pdf_to_single_txt(PDF_DIR, OUTPUT_TXT)