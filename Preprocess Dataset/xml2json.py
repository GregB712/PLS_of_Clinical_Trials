import xml.etree.ElementTree as ET
import json
import re
import os
import sys

def parse_xml_sections(xml_file, section_titles):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    sections = {}
    
    for section in root.findall('section'):
        name = section.get('name')
        if name in section_titles:
            lines = list(section.itertext())
            # Exclude the first line and remove lines matching the pattern
            filtered_lines = [line for line in lines[1:] if not re.match(r'.* or .* Summary \| \d+', line)]
            text_content = "".join(filtered_lines)
            sections[name] = text_content.strip()
    
    return sections

def create_json(data, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python xml2json.py <trials_dir> <summaries_dir>")
        sys.exit(1)

    trials_dir = sys.argv[1]
    summaries_dir = sys.argv[2]
    
    trial_section_titles = [
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

    summary_section_titles = [
        "What adverse events did participants report?",
        "What non-serious adverse events did participants have?",
        "What were the results of the trial?",
        "What medical problems did patients have?",
        "How has this trial helped?",
        "What happened during the trial?",
        "What treatments did the participants take?",
        "What other results were learned?",
        "Who was in this clinical trial?",
        "What kind of trial was this?",
        "What was the purpose of this clinical trial?",
        "Why was the research needed?", 
        "How long was the trial?", 
        "How many participants stopped trial drug due to adverse events?", 
        "How this trial was designed", 
        "What has happened since the trial ended?",
        "Where can I learn more about this trial?",
        "Thank you"
        ]

    data = []

    # Collect all trial and summary files
    trial_files = [f for f in os.listdir(trials_dir) if os.path.isfile(os.path.join(trials_dir, f))]
    summary_files = [f for f in os.listdir(summaries_dir) if os.path.isfile(os.path.join(summaries_dir, f))]

    # Match trial and summary files based on their common ID
    for trial_filename in trial_files:
        trial_id, trial_ext = os.path.splitext(trial_filename)
        trial_file_path = os.path.join(trials_dir, trial_filename)
        
        matched_summary_file = None
        for summary_filename in summary_files:
            if summary_filename.startswith(trial_id):
                matched_summary_file = summary_filename
                break
        
        if matched_summary_file:
            summary_file_path = os.path.join(summaries_dir, matched_summary_file)
            
            trial_sections = parse_xml_sections(trial_file_path, trial_section_titles)
            summary_sections = parse_xml_sections(summary_file_path, summary_section_titles)

            print(f"Currently parsing trial/summary: '{trial_id}'")
            
            entry = {
                "trial_name": trial_id,
                "trial_file_path": trial_file_path,
                "summary_file_path": summary_file_path,
                "trial": trial_sections,
                "summary": summary_sections
            }
            
            data.append(entry)

    output_json_file = "database.json"
    create_json(data, output_json_file)

    print(f"JSON file '{output_json_file}' has been created with the specified sections from all trials and summaries.")
