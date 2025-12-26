"""
PDF processing module for extracting tables from PDF files
"""
import io
import logging
from typing import List, Dict, Any, Optional, Union
import pdfplumber

logger = logging.getLogger(__name__)

async def extract_table_from_pdf(file_data: bytes, student_id: Optional[str] = None) -> List[List[List[str]]]:
    """
    Extract all tables from a PDF file
    
    Args:
        file_data: PDF file content as bytes
        
    Returns:
        List of tables, where each table is a list of rows,
        and each row is a list of cell values
    """
    try:
        # Create a file-like object from bytes
        pdf_stream = io.BytesIO(file_data)
        
        all_tables = []
        
        with pdfplumber.open(pdf_stream) as pdf:
            logger.info(f"Processing PDF with {len(pdf.pages)} pages")
            
            # Optimize: Process pages in chunks for better memory management
            for page_num, page in enumerate(pdf.pages):
                # Extract tables from the current page
                tables = page.extract_tables()
                
                if tables:
                    logger.info(f"Found {len(tables)} table(s) on page {page_num + 1}")
                    
                    for table_num, table in enumerate(tables):
                        if table and len(table) > 1:
                            # Clean the table data
                            cleaned_table = clean_table(table)
                            if cleaned_table:
                                all_tables.append(cleaned_table)
                                
                                # Early exit optimization: if student_id provided, check if found
                                if student_id and quick_check_student_in_table(cleaned_table, student_id):
                                    logger.info(f"Found student ID early on page {page_num + 1}, stopping extraction")
                                    return all_tables
        
        logger.info(f"Total tables extracted: {len(all_tables)}")
        return all_tables
        
    except Exception as e:
        logger.error(f"Error extracting tables from PDF: {e}")
        raise Exception(f"Failed to process PDF file: {str(e)}")

def clean_table(raw_table: List[List[Union[str, None]]]) -> Optional[List[List[str]]]:
    """
    Clean and validate table data
    
    Args:
        raw_table: Raw table data from pdfplumber
        
    Returns:
        Cleaned table data or None if invalid
    """
    try:
        if not raw_table or len(raw_table) < 2:
            return None
        
        cleaned_table = []
        
        for row in raw_table:
            if not row:
                continue
                
            # Clean each cell in the row
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # Strip whitespace and normalize
                    cleaned_cell = str(cell).strip()
                    cleaned_row.append(cleaned_cell)
            
            # Only add rows that have at least one non-empty cell
            if any(cell for cell in cleaned_row):
                cleaned_table.append(cleaned_row)
        
        # Validate that we have at least a header and one data row
        if len(cleaned_table) < 2:
            logger.warning("Table has insufficient rows after cleaning")
            return None
        
        # Check if the table looks like it contains names and grades
        if not is_grade_table(cleaned_table):
            logger.warning("Table doesn't appear to contain grade information")
        
        return cleaned_table
        
    except Exception as e:
        logger.error(f"Error cleaning table: {e}")
        return None

def is_grade_table(table: List[List[str]]) -> bool:
    """
    Heuristic check to determine if a table contains grade information
    
    Args:
        table: Cleaned table data
        
    Returns:
        True if table appears to contain grades
    """
    try:
        if not table or len(table) < 2:
            return False
        
        # Check header row for grade-related keywords
        header = [cell.lower() for cell in table[0] if cell]
        grade_keywords = ['grade', 'score', 'mark', 'result', 'points', 'percentage', '%']
        name_keywords = ['name', 'student', 'roll', 'id', 'number']
        
        has_grade_column = any(keyword in ' '.join(header) for keyword in grade_keywords)
        has_name_column = any(keyword in ' '.join(header) for keyword in name_keywords)
        
        # Check data rows for patterns that look like grades
        grade_patterns = 0
        name_patterns = 0
        
        for row in table[1:5]:  # Check first few data rows
            if not row:
                continue
                
            for cell in row:
                if not cell:
                    continue
                    
                cell_str = str(cell).strip()
                
                # Check for grade patterns (numbers, letter grades, pass/fail)
                if (cell_str.replace('.', '').replace(',', '').isdigit() or
                    cell_str.upper() in ['A', 'B', 'C', 'D', 'F', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'D+', 'D-'] or
                    cell_str.lower() in ['pass', 'fail', 'passed', 'failed'] or
                    '%' in cell_str):
                    grade_patterns += 1
                
                # Check for name patterns (contains letters and possibly spaces)
                if (len(cell_str) > 2 and 
                    any(c.isalpha() for c in cell_str) and
                    not cell_str.replace('.', '').replace(',', '').isdigit()):
                    name_patterns += 1
        
        # Table is likely a grade table if it has both name and grade patterns
        result = (has_grade_column or grade_patterns > 0) and (has_name_column or name_patterns > 0)
        
        logger.debug(f"Grade table check: has_grade_column={has_grade_column}, "
                    f"has_name_column={has_name_column}, grade_patterns={grade_patterns}, "
                    f"name_patterns={name_patterns}, result={result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking if table contains grades: {e}")
        return True  # Default to True to be permissive

def quick_check_student_in_table(table: List[List[str]], student_id: str) -> bool:
    """
    Quick check if student ID exists in table for early exit optimization
    
    Args:
        table: Cleaned table data
        student_id: Student ID to search for
        
    Returns:
        True if student ID found in table
    """
    if not table or len(table) < 2:
        return False
    
    try:
        # Assume ID is in second column from right
        max_cols = len(table[0]) if table[0] else 0
        if max_cols < 2:
            return False
            
        id_col_idx = max_cols - 2
        
        # Quick scan for student ID
        for row in table[1:]:  # Skip header
            if id_col_idx < len(row) and str(row[id_col_idx]).strip() == student_id:
                return True
        
        return False
    except Exception:
        return False
