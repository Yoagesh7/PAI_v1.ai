from fpdf import FPDF
import os
import string

def sanitize_text(text):
    # Only allow characters between space (32) and ~ (126)
    return ''.join(c for c in text if 32 <= ord(c) <= 126)

def create_pdf(input_md, output_pdf):
    # A4 is 210mm wide. 20mm margins left/right -> 170mm width.
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(left=20, top=20, right=20)
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 18)
    pdf.multi_cell(w=170, h=15, text='PartnerAI - Project Technical Specification', align='C')
    pdf.ln(10)
    
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by lines
    lines = content.split('\n')

    pdf.set_font("Helvetica", size=11)
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue
            
        line = sanitize_text(line)
        if not line: continue
        
        # Ensure we are not near the bottom or right edge weirdly
        pdf.set_x(20) 
        
        try:
            if line.startswith('# '):
                pdf.ln(5)
                pdf.set_font("Helvetica", 'B', 16)
                pdf.multi_cell(w=170, h=10, text=line[2:])
                pdf.set_font("Helvetica", size=11)
            elif line.startswith('## '):
                pdf.ln(3)
                pdf.set_font("Helvetica", 'B', 14)
                pdf.multi_cell(w=170, h=10, text=line[3:])
                pdf.set_font("Helvetica", size=11)
            elif line.startswith('### '):
                pdf.set_font("Helvetica", 'B', 12)
                pdf.multi_cell(w=170, h=8, text=line[4:])
                pdf.set_font("Helvetica", size=11)
            elif line.startswith('- ') or line.startswith('* '):
                pdf.multi_cell(w=170, h=7, text=f'  - {line[2:]}')
            elif line.startswith('---'):
                pdf.ln(2)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(4)
            else:
                clean_line = line.replace('**', '').replace('> [!NOTE]', 'NOTE:').replace('> ', '')
                pdf.multi_cell(w=170, h=7, text=clean_line)
        except Exception as e:
            print(f"FAILED on line {i}: {line[:50]}...")
            print(f"Error: {e}")
            # Try to continue or break
            continue

    pdf.output(output_pdf)
    print(f"Successfully generated {output_pdf}")

if __name__ == "__main__":
    md_path = r"C:\Users\yo405\.gemini\antigravity\brain\6ae79f5a-8083-44b1-9291-882c0550a4ee\PartnerAI_Blueprint.md"
    pdf_path = r"e:\PartnerAI\PartnerAI_Project_Full_Data.pdf"
    create_pdf(md_path, pdf_path)
