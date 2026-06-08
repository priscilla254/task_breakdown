"""
Generate tasks-training.json: each module -> Content (7h) + Development (14h).
Development depends on its content; dev tasks chain serially (one module at a time).
"""
import json
from pathlib import Path

# (module_name, subject, department) — order defines dev sequence
MODULES = [
    ("What is our standard?", "Introduction / The Costplan Way", "Group"),
    ("Our Values", "Introduction / The Costplan Way", "Group"),
    ("Office Culture", "Introduction / The Costplan Way", "Group"),
    ("Professionalism", "Introduction / The Costplan Way", "Group"),
    ("Communication generally", "Communications", "Group"),
    ("Phone First", "Communications", "Group"),
    ("Meeting preparation", "Communications", "Group"),
    ("How to take Meeting Minutes", "Communications", "Group"),
    ("Teams meeting etiquette", "Communications", "Group"),
    ("Letter Writing", "Communications", "Group"),
    ("Email etiquette", "Communications", "Group"),
    ("Efficiencies explained", "Time / efficiencies", "Group"),
    ("WorkflowMax use", "Time / efficiencies", "Group"),
    ("Dropbox", "Document & Quality Control", "Group"),
    ("File naming conventions", "Document & Quality Control", "Group"),
    ("Record keeping", "Document & Quality Control", "Group"),
    ("Quality Assurance", "Document & Quality Control", "Group"),
    ("Diversity & Inclusion", "HR", "Group"),
    ("bullying and harrassment", "HR", "Group"),
    ("Measurement rules", "General Requirements", "Quantity Surveying"),
    ("Software selection", "General Requirements", "Quantity Surveying"),
    ("Drawings scales", "General Requirements", "Quantity Surveying"),
    ("Understanding RICS Competencies", "General Requirements", "Quantity Surveying"),
    ("Quality Assurance - Generally", "General Requirements", "Quantity Surveying"),
    ("Quality Assurance - Costplan QA processes", "General Requirements", "Quantity Surveying"),
    ("Query sheets", "General Requirements", "Quantity Surveying"),
    ("Record keeping", "General Requirements", "Quantity Surveying"),
    ("Appointments", "Project Establishment", "Quantity Surveying"),
    ("Insurances", "Project Establishment", "Quantity Surveying"),
    ("Client Brief", "Project Establishment", "Quantity Surveying"),
    ("Deliverables", "Project Establishment", "Quantity Surveying"),
    ("Defining our Scope of Work", "Project Establishment", "Quantity Surveying"),
    ("Procurement selection", "Procurement", "Quantity Surveying"),
    ("Types and Tender Docs associated", "Procurement", "Quantity Surveying"),
    ("Selection of contract", "Procurement", "Quantity Surveying"),
    ("PCSA's", "Procurement", "Quantity Surveying"),
    ("Single Stage", "Procurement", "Quantity Surveying"),
    ("Two Stage", "Procurement", "Quantity Surveying"),
    ("Frameworks", "Procurement", "Quantity Surveying"),
    ("Prime Cost", "Procurement", "Quantity Surveying"),
    ("CM etc", "Procurement", "Quantity Surveying"),
    ("Contract Administration", "Construction", "Quantity Surveying"),
    ("Key Contract Information", "Construction", "Quantity Surveying"),
    ("Valuations", "Construction", "Quantity Surveying"),
    ("Variations", "Construction", "Quantity Surveying"),
    ("Warranties / Insurances", "Construction", "Quantity Surveying"),
    ("Introduction; purpose", "Planning Process", "Planning and Programming"),
    ("Planning Basics", "Planning Process", "Planning and Programming"),
    ("Document appraisal", "Planning Process", "Planning and Programming"),
    ("Cascade analysis", "Planning Process", "Planning and Programming"),
    ("Strategy", "Planning Process", "Planning and Programming"),
    ("PFD presentation", "Planning Process", "Planning and Programming"),
    ("PFD - Stage 1", "Planning Process", "Planning and Programming"),
    ("Gantt charts -1", "Planning Process", "Planning and Programming"),
    ("Programme - Stage 2", "Planning Process", "Planning and Programming"),
    ("Programme - Stage 3", "Planning Process", "Planning and Programming"),
    ("Industry Processes [RIBA, Highways, Rail, Nuclear, …]", "Programme development", "Planning and Programming"),
    ("Selection of appropriate format", "Programme development", "Planning and Programming"),
    ("Gantt charts -2", "Programme development", "Planning and Programming"),
    ("Use of Computer Gantt", "Programme development", "Planning and Programming"),
    ("Outputs", "Programme development", "Planning and Programming"),
    ("Conditions, Constraints & Requirements", "Programme development", "Planning and Programming"),
    ("Calendars - Time", "Programme development", "Planning and Programming"),
    ("Critical Path/ Longest Path; Float paths", "Programme development", "Planning and Programming"),
    ("Float; type, function, analysis, presentation", "Programme development", "Planning and Programming"),
    ("Baselines", "Programme development", "Planning and Programming"),
    ("QSRA / Monte Carlo - Risk & Uncertainty", "Risk & Opportunity", "Planning and Programming"),
    ("Definitions & interpretations", "Risk & Opportunity", "Planning and Programming"),
    ("TRA", "Risk & Opportunity", "Planning and Programming"),
    ("Project Risk Schedule", "Risk & Opportunity", "Planning and Programming"),
    ("Value Engineering", "Risk & Opportunity", "Planning and Programming"),
    ("Function", "Temporary Works", "Planning and Programming"),
    ("Selection / options", "Temporary Works", "Planning and Programming"),
    ("Construction Methods Highrise", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Residential", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Data Centres", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Hospital", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - School/ education", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Rail", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Cable", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Pipeline", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Structures", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Highways", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Marine", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Water Treatment", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Sewage Treatment", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Nuclear", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - General Groundworks", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - Airports", "Construction Methods", "Planning and Programming"),
    ("Construction Methods - River/ canal/ Reservoir", "Construction Methods", "Planning and Programming"),
    ("Methods of measurement", "Cost Management", "Planning and Programming"),
    ("CostX interface", "Cost Management", "Planning and Programming"),
    ("BoQ interface", "Cost Management", "Planning and Programming"),
    ("Activity Schedule Interface", "Cost Management", "Planning and Programming"),
    ("Allocation", "Cost Management", "Planning and Programming"),
    ("Analysis : SPI/CPI ? EVM", "Cost Management", "Planning and Programming"),
    ("Recording", "Progress", "Planning and Programming"),
    ("Processing", "Progress", "Planning and Programming"),
    ("Analysis", "Progress", "Planning and Programming"),
    ("Presentation", "Progress", "Planning and Programming"),
    ("Procurement Tracking", "Progress", "Planning and Programming"),
    ("Requirements", "Project Management", "Planning and Programming"),
    ("Psychology", "Project Management", "Planning and Programming"),
    ("Project teams", "Project Management", "Planning and Programming"),
    ("Activity Day Count - S-Curve ; Burn-down,..", "Project Controls", "Planning and Programming"),
    ("KPIs for key trades (under proejct controls)", "Project Controls", "Planning and Programming"),
    ("Lead & Lag indicators", "Project Controls", "Planning and Programming"),
    ("Managing EW's", "Managing Change", "Planning and Programming"),
    ("Impacting programme with CE", "Managing Change", "Planning and Programming"),
    ("Claims [EoT] Methods", "Managing Change", "Planning and Programming"),
    ("PDF", "Assessment of Programmes", "Planning and Programming"),
    ("Live File", "Assessment of Programmes", "Planning and Programming"),
    ("NEC: 3,4", "Forms of Contract", "Planning and Programming"),
    ("JCT", "Forms of Contract", "Planning and Programming"),
    ("FIDIC", "Forms of Contract", "Planning and Programming"),
    ("Modified/ bespoke", "Forms of Contract", "Planning and Programming"),
    ("Time Chainage/ Time - Location", "Programme Formats", "Planning and Programming"),
    ("Line of Balance", "Programme Formats", "Planning and Programming"),
    ("Gantt", "Programme Formats", "Planning and Programming"),
    ("Powerproject - Asta", "Software Packages", "Planning and Programming"),
    ("Primavera", "Software Packages", "Planning and Programming"),
    ("MSP (MS Project)", "Software Packages", "Planning and Programming"),
    ("Excel", "Software Packages", "Planning and Programming"),
    ("Bespoke", "Software Packages", "Planning and Programming"),
    ("Design Programme", "Function Programmes", "Planning and Programming"),
    ("Procurement Programme", "Function Programmes", "Planning and Programming"),
    ("Completion", "Function Programmes", "Planning and Programming"),
    ("As-Built", "Function Programmes", "Planning and Programming"),
    ("Format Selection", "Methodology", "Planning and Programming"),
    ("Sequencing", "Methodology", "Planning and Programming"),
    ("Presentation", "Methodology", "Planning and Programming"),
    ("Scenario's", "Methodology", "Planning and Programming"),
    ("P1686_East Road - Hackney , Time-Cost", "Reference", "Planning and Programming"),
    ("P1490_1-3 Whitefriars_Canterbury", "Reference", "Planning and Programming"),
    ("P2034_Wye Wetlands", "Reference", "Planning and Programming"),
    ("Site visits", "General Requirements", "Safety"),
    ("PPE", "General Requirements", "Safety"),
    ("Contacts for safety", "General Requirements", "Safety"),
    ("Slips trips & falls", "Site Safety", "Safety"),
    ("Excavations", "Site Safety", "Safety"),
    ("Risk Assessments", "Site Safety", "Safety"),
    ("Method Statements", "Site Safety", "Safety"),
    ("Person in control", "Site Safety", "Safety"),
    ("Training Requirements / scope", "Scope", "Training & Development"),
    ("Compiling a syllabus", "Delivery", "Training & Development"),
    ("Compiling training sessions", "Delivery", "Training & Development"),
    ("Venue organisation", "Delivery", "Training & Development"),
    ("Feedback", "Development", "Training & Development"),
    ("Action Plans", "Development", "Training & Development"),
    ("what skills a manager requires", "Management", "Training & Development"),
    ("Training Requirements / scope", "Scope", "Administration"),
    ("How to run payroll (safeHr)", "Delivery", "Administration"),
    ("Guide to chasing invoices and downloadin the relevant info", "Delivery", "Administration"),
    ("Guide for completing expenses via safeHR", "Delivery", "Administration"),
    ("Guide to create P&Q numbers", "Delivery", "Administration"),
    ("How to submit and complete newsletter information", "Delivery", "Administration"),
    ("How to conduct an Interview", "Delivery", "Administration"),
    ("Bullying and harrassment", "Delivery", "Administration"),
]

CONTENT_HOURS = 7
DEV_HOURS = 14
N = len(MODULES)
assert N == 158, f"Expected 158 modules, got {N}"


def main():
    tasks = []
    prev_dev_id = None

    for i, (name, subject, department) in enumerate(MODULES, start=1):
        content_id = i
        dev_id = N + i

        tasks.append(
            {
                "id": content_id,
                "task": f"{name} — Content",
                "hours": CONTENT_HOURS,
                "department": department,
                "subject": subject,
                "phase": "content",
                "module_index": i,
                "depends_on": [],
                "status": "Not started",
                "log": "",
            }
        )

        dev_deps = [content_id]
        if prev_dev_id is not None:
            dev_deps.append(prev_dev_id)

        tasks.append(
            {
                "id": dev_id,
                "task": f"{name} — Development",
                "hours": DEV_HOURS,
                "department": department,
                "subject": subject,
                "phase": "development",
                "module_index": i,
                "depends_on": dev_deps,
                "status": "Not started",
                "log": "",
            }
        )
        prev_dev_id = dev_id

    payload = {
        "project_start": "2026-06-01",
        "gap_days": 1,
        "tasks": tasks,
    }

    out = Path(__file__).resolve().parent.parent / "data" / "tasks-training.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(tasks)} tasks ({N} modules) to {out}")


if __name__ == "__main__":
    main()
