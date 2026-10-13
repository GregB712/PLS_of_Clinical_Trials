
import os
import sys
import re
import xml.etree.ElementTree as ET
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTChar

class ClinicalTrial:
    def __init__(self, variable):
        self.variable = variable
        # List of sections to recognize
        self._SECTIONS = [
            "Generic Drug Name",
            "Protocol Number",
            "Study Start/End Dates",
            "Reason for Termination",
            "Study Design/Methodology",
            "Centers",
            "Objectives",
            "Test Product(s), Dose(s), and Mode(s) of Administration",
            "Statistical Methods",
            "Study Population: Key Inclusion/Exclusion Criteria",
            "Participant Flow Table",
            "Baseline Characteristics",
            "Primary Outcome Result(s)",
            "Secondary Outcome Result(s)",
            "Summary of Safety",
            "Safety Results",
            "All-Cause Mortality",
            "Serious Adverse Events",
            "Other .* Adverse Events",
            "Other Relevant Findings",
            "Conclusion",
            "Date of Clinical Trial Report"
        ]

        # Sections that contain table structures
        self._TABLE_SECTIONS = [
            "Participant Flow Table",
            "Baseline Characteristics",
            "Primary Outcome Result(s)",
            "Secondary Outcome Result(s)",
            "All-Cause Mortality",
            "Serious Adverse Events",
            "Other .* Adverse Events"
        ]

        # Compile regex patterns for each section
        self._section_patterns = {section: re.compile(section, re.IGNORECASE) for section in self._SECTIONS}
        self._page_number_pattern = re.compile(r'Page \d+', re.IGNORECASE)

    def get_text_properties(self, text_line):
        bold = italic = underline = False
        for character in text_line:
            if isinstance(character, LTChar):
                fontname = character.fontname.lower()
                if 'bold' in fontname:
                    bold = True
                if 'italic' in fontname or 'oblique' in fontname:
                    italic = True
                if 'underline' in fontname:
                    underline = True
        return bold, italic, underline

    def detect_section(self, text, bold):
        if not bold:
            return None
        for section, pattern in self._section_patterns.items():
            if pattern.search(text):
                return section
        return None

    def pdf_to_xml(self, pdf_path, xml_path):
        # Create the root element
        root = ET.Element("document")

        # Combine all PDF content into a single logical page
        all_text_elements = []

        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal):
                    for text_line in element:
                        text = text_line.get_text().strip()
                        # Skip lines containing page numbering
                        if self._page_number_pattern.search(text):
                            continue
                        all_text_elements.append((text_line, text))

        # Process the combined content
        current_section = None
        section_element = None
        inside_table_section = False

        for text_line, text in all_text_elements:
            # Skip lines containing "Clinical Trial Results Website"
            if "Clinical Trial Results Website" in text:
                continue

            # Get the properties of the text line
            bold, italic, underline = self.get_text_properties(text_line)

            # Detect section
            new_section = self.detect_section(text, bold)
            if new_section:
                current_section = new_section
                section_element = ET.SubElement(root, "section", name=current_section)
                inside_table_section = any(re.search(pattern, current_section, re.IGNORECASE) for pattern in self._TABLE_SECTIONS)

            if inside_table_section:
                if not text:  # skip empty lines
                    continue

                # Create or continue a table element
                if not any(child.tag == 'table' for child in section_element):
                    table_element = ET.SubElement(section_element, "table")
                else:
                    table_element = section_element.find("table")

                # Create a row element within the table
                row_element = ET.SubElement(table_element, "row")
                cell_element = ET.SubElement(row_element, "cell")
                cell_element.text = text
            else:
                # Create a line element within the current section
                if section_element is None:
                    section_element = ET.SubElement(root, "section", name="Uncategorized")

                line_element = ET.SubElement(section_element, "line")
                if bold:
                    line_element.set('bold', 'yes')
                if italic:
                    line_element.set('italic', 'yes')
                if underline:
                    line_element.set('underline', 'yes')
                line_element.text = text

        # Create a tree structure
        tree = ET.ElementTree(root)

        # Write the tree to an XML file
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        print(f"PDF content successfully written to {xml_path}")
        print(f"Class Clinical Trial, pdf_to_xml executed on {pdf_path} with variable {self.variable}")

class PatientSummary:
    def __init__(self, variable):
        self.variable = variable
        # List of sections to recognize
        self._SECTIONS = [
            "Did any patients have serious adverse events?",
            "How many participants had adverse events?",
            "How many participants reported serious adverse events?",
            "How many patients had adverse events during the trial?",
            "What adverse events did participants report?",
            "What adverse events did the participants have?",
            "What serious adverse events did participants have?",
            "What serious adverse events did the participants have?",
            "What was the most common serious adverse event?",
            "What were the most common serious adverse events?",
            "What were the serious adverse events?",
            "What non-serious adverse events did participants have?",
            "What other adverse events did the participants have?",
            "What was the most common non-serious adverse event?",
            "What were the most common non-serious adverse events?",
            "What were the non-serious adverse events?",
            "What were the results of the trial?",
            "What were the results of this study?",
            "What were the key results of this trial?",
            "What were the main results of the trial?",
            "What were the main results of this clinical trial?",
            "What were the main results of this trial?",
            "What was the main result of this trial?",
            "What was learned from this trial?",
            "What medical problems did patients have?",
            "What medical problems did the participants have during the entire trial, up to Week 60?",
            "What medical problems did the participants have during the trial?",
            "What medical problems happened during the trial?",
            "How has this clinical trial helped patients and researchers?",
            "How has this trial helped patients and researchers?",
            "How has this trial helped?",
            "How was this trial useful?",
            "What happened during the trial?",
            "What happened during this clinical trial?",
            "What happened during this trial?",
            "What treatments did the participants receive?",
            "What treatments did the participants take?",
            "What trial treatments did the participants take?",
            "What other key results were learned?",
            "What other results were learned?",
            "What were the other results of this trial?",
            "Who was in the trial?",
            "Who was in this clinical trial?",
            "Who was in this trial?",
            "What kind of trial was this?",
            "What type of clinical trial was this?",
            "What was the purpose of this clinical trial?",
            "What was the purpose of this trial?",
            "What was the main purpose of this trial?",
            "What was the goal of this observational study?",
            "Why was the research needed?",
            "How long was the trial?",
            "How long was this trial?",
            "How many participants stopped trial drug due to adverse events?",
            "How this trial was designed",
            "What has happened since the trial ended?",
            "Where can I learn more about this trial?",
            "Thank you"
        ]

        self._mappingSections = {
            "Did any patients have serious adverse events?": "What adverse events did participants report?",
            "How many participants had adverse events?": "What adverse events did participants report?",
            "How many participants reported serious adverse events?": "What adverse events did participants report?",
            "How many patients had adverse events during the trial?": "What adverse events did participants report?",
            "What adverse events did participants report?": "What adverse events did participants report?",
            "What adverse events did the participants have?": "What adverse events did participants report?",
            "What serious adverse events did participants have?": "What adverse events did participants report?",
            "What serious adverse events did the participants have?": "What adverse events did participants report?",
            "What was the most common serious adverse event?": "What adverse events did participants report?",
            "What were the most common serious adverse events?": "What adverse events did participants report?",
            "What were the serious adverse events?": "What adverse events did participants report?",
            "What non-serious adverse events did participants have?": "What non-serious adverse events did participants have?",
            "What other adverse events did the participants have?": "What non-serious adverse events did participants have?",
            "What was the most common non-serious adverse event?": "What non-serious adverse events did participants have?",
            "What were the most common non-serious adverse events?": "What non-serious adverse events did participants have?",
            "What were the non-serious adverse events?": "What non-serious adverse events did participants have?",
            "What were the results of the trial?": "What were the results of the trial?",
            "What were the results of this study?": "What were the results of the trial?",
            "What were the key results of this trial?": "What were the results of the trial?",
            "What were the main results of the trial?": "What were the results of the trial?",
            "What were the main results of this clinical trial?": "What were the results of the trial?",
            "What were the main results of this trial?": "What were the results of the trial?",
            "What was the main result of this trial?": "What were the results of the trial?",
            "What was learned from this trial?": "What were the results of the trial?",
            "What medical problems did patients have?": "What medical problems did patients have?",
            "What medical problems did the participants have during the entire trial, up to Week 60?": "What medical problems did patients have?",
            "What medical problems did the participants have during the trial?": "What medical problems did patients have?",
            "What medical problems happened during the trial?": "What medical problems did patients have?",
            "How has this clinical trial helped patients and researchers?": "How has this trial helped?",
            "How has this trial helped patients and researchers?": "How has this trial helped?",
            "How has this trial helped?": "How has this trial helped?",
            "How was this trial useful?": "How has this trial helped?",
            "What happened during the trial?": "What happened during the trial?",
            "What happened during this clinical trial?": "What happened during the trial?",
            "What happened during this trial?": "What happened during the trial?",
            "What treatments did the participants receive?": "What treatments did the participants take?",
            "What treatments did the participants take?": "What treatments did the participants take?",
            "What trial treatments did the participants take?": "What treatments did the participants take?",
            "What other key results were learned?": "What other results were learned?",
            "What other results were learned?": "What other results were learned?",
            "What were the other results of this trial?": "What other results were learned?",
            "Who was in the trial?": "Who was in this clinical trial?",
            "Who was in this clinical trial?": "Who was in this clinical trial?",
            "Who was in this trial?": "Who was in this clinical trial?",
            "What kind of trial was this?": "What kind of trial was this?",
            "What type of clinical trial was this?": "What kind of trial was this?",
            "What was the purpose of this clinical trial?": "What was the purpose of this clinical trial?",
            "What was the purpose of this trial?": "What was the purpose of this clinical trial?",
            "What was the main purpose of this trial?": "What was the purpose of this clinical trial?",
            "What was the goal of this observational study?": "What was the purpose of this clinical trial?",
            "Why was the research needed?": "Why was the research needed?", 
            "How long was the trial?": "How long was the trial?", 
            "How long was this trial?": "How long was the trial?",
            "How many participants stopped trial drug due to adverse events?": "How many participants stopped trial drug due to adverse events?", 
            "How this trial was designed": "How this trial was designed", 
            "What has happened since the trial ended?": "What has happened since the trial ended?",
            "Where can I learn more about this trial?": "Where can I learn more about this trial?",
            "Thank you": "Thank you"
        }

        # Sections that contain table structures
        self._TABLE_SECTIONS = []

        # Compile regex patterns for each section
        self._section_patterns = {section: re.compile(section, re.IGNORECASE) for section in self._SECTIONS}
        self._page_number_pattern = re.compile(r'Page \d+', re.IGNORECASE)

    def get_text_properties(self, text_line):
        bold = italic = underline = False
        for character in text_line:
            if isinstance(character, LTChar):
                fontname = character.fontname.lower()
                if 'bold' in fontname:
                    bold = True
                if 'italic' in fontname or 'oblique' in fontname:
                    italic = True
                if 'underline' in fontname:
                    underline = True
        return bold, italic, underline

    def detect_section(self, text, bold):
        if not bold:
            return None
        for section, pattern in self._section_patterns.items():
            if pattern.search(text):
                return self._mappingSections.get(section)
        return None

    def pdf_to_xml(self, pdf_path, xml_path):
        # Create the root element
        root = ET.Element("document")

        # Combine all PDF content into a single logical page
        all_text_elements = []

        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal):
                    for text_line in element:
                        text = text_line.get_text().strip()
                        # Skip lines containing page numbering
                        if self._page_number_pattern.search(text):
                            continue
                        all_text_elements.append((text_line, text))

        # Process the combined content
        current_section = None
        section_element = None
        inside_table_section = False

        for text_line, text in all_text_elements:
            # Skip lines containing "Clinical Trial Results Website"
            if "Clinical Trial Results Website" in text:
                continue

            # Get the properties of the text line
            bold, italic, underline = self.get_text_properties(text_line)

            # Detect section
            new_section = self.detect_section(text, bold)
            if new_section:
                current_section = new_section
                section_element = ET.SubElement(root, "section", name=current_section)
                inside_table_section = any(re.search(pattern, current_section, re.IGNORECASE) for pattern in self._TABLE_SECTIONS)

            if inside_table_section:
                if not text:  # skip empty lines
                    continue

                # Create or continue a table element
                if not any(child.tag == 'table' for child in section_element):
                    table_element = ET.SubElement(section_element, "table")
                else:
                    table_element = section_element.find("table")

                # Create a row element within the table
                row_element = ET.SubElement(table_element, "row")
                cell_element = ET.SubElement(row_element, "cell")
                cell_element.text = text
            else:
                # Create a line element within the current section
                if section_element is None:
                    section_element = ET.SubElement(root, "section", name="Uncategorized")

                line_element = ET.SubElement(section_element, "line")
                if bold:
                    line_element.set('bold', 'yes')
                if italic:
                    line_element.set('italic', 'yes')
                if underline:
                    line_element.set('underline', 'yes')
                line_element.text = text

        # Create a tree structure
        tree = ET.ElementTree(root)

        # Write the tree to an XML file
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        print(f"PDF content successfully written to {xml_path}")
        print(f"Class Patient Summary, pdf_to_xml executed on {pdf_path} with variable {self.variable}")

def replace_suffix(file_name):
    if file_name.endswith(".pdf"):
        return file_name[:-4] + ".xml"
    else:
        return file_name

def process_files(directory, variable):
    if not os.path.isdir(directory):
        print(f"The provided path '{directory}' is not a directory.")
        return

    # List all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Determine the class and method based on the variable
    if variable == 'ct':
        chosen_instance = ClinicalTrial(variable)
    else:
        chosen_instance = PatientSummary(variable)

    # Apply the chosen method to all files
    for file in files:
        file_path = os.path.join(directory, file)
        xml_path = replace_suffix(file_path)
        print(f"Now Parsing:'{file}'")
        chosen_instance.pdf_to_xml(file_path, xml_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parser.py <directory_path> <variable>")
        sys.exit(1)

    directory_path = sys.argv[1]
    variable = sys.argv[2]
    
    process_files(directory_path, variable)
