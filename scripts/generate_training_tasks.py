"""
Generate tasks-training.json: each module → 15 subtasks across 3 phases.

ID scheme:  module_index * 100 + step_offset
  1.1 → +1,  1.2 → +2,  1.3 → +3,  1.4 → +4,  1.5 → +5
  2.1 → +11, 2.2 → +12, 2.3 → +13
  2.4 → +14, 2.5 → +15, 2.6 → +16 (parallel qa group)
  2.7 → +17, 2.8 → +18
  3.1 → +21, 3.2 → +22, 3.3 → +23 (parallel upload group)

Rolling tier rule (module N+1 assign step 1.1):
  starts_with = module N step 1.5 (management content approval start)
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

N = len(MODULES)


def tid(mod_idx: int, offset: int) -> int:
    return mod_idx * 100 + offset


def make_module(mod_idx: int, name: str, subject: str, department: str,
                prev_approval_id: int | None,
                prev_dev_approval_id: int | None) -> list:
    """Return all tasks for one module with correct dependencies."""

    # Content phase IDs
    t11 = tid(mod_idx, 1)
    t12 = tid(mod_idx, 2)
    t13 = tid(mod_idx, 3)
    t14 = tid(mod_idx, 4)
    t15 = tid(mod_idx, 5)

    # Development phase IDs
    t21 = tid(mod_idx, 11)
    t22 = tid(mod_idx, 12)
    t23 = tid(mod_idx, 13)
    t24 = tid(mod_idx, 14)
    t25 = tid(mod_idx, 15)
    t26 = tid(mod_idx, 16)
    t27 = tid(mod_idx, 17)
    t28 = tid(mod_idx, 18)

    # Upload phase IDs
    t31 = tid(mod_idx, 21)
    t32 = tid(mod_idx, 22)
    t33 = tid(mod_idx, 23)

    meta = dict(department=department, subject=subject, module_index=mod_idx)

    def task(id_, step_id, task_name, phase, days, assignee, depends_on,
             parallel_group=None, milestone=False, starts_with=None):
        t = {
            "id": id_,
            "task": f"{name} - {task_name}",
            "status": "Not started",
            "log": "",
            "depends_on": depends_on,
            "days": days,
            "phase": phase,
            "step_id": step_id,
            **meta,
        }
        if assignee:
            t["assignee"] = assignee
        if parallel_group:
            t["parallel_group"] = parallel_group
        if milestone:
            t["milestone"] = True
        if starts_with is not None:
            t["starts_with"] = starts_with
        return t

    # Module N+1 assign (1.1) starts when module N content approval (1.5) starts.
    t11_starts_with = prev_approval_id  # None for module 1

    tasks = [
        task(t11, "1.1", "Assign the training", "content", 0, "Priscilla", [],
             milestone=True, starts_with=t11_starts_with),
        task(t12, "1.2", "Populate the word document", "content", 5, "Priscilla", [t11]),
        task(t13, "1.3", "Review and comment", "content", 1, "Priscilla", [t12],
             parallel_group=f"m{mod_idx}-content-review"),
        task(t14, "1.4", "Update to word", "content", 1, "Priscilla", [t12],
             parallel_group=f"m{mod_idx}-content-review"),
        task(t15, "1.5", "Approval of word document", "content", 3, None, [t13, t14]),

        task(t21, "2.1", "Design slides", "development", 1, "Priscilla", [t15]),
        task(t22, "2.2", "Input slide content", "development", 0.5, "Priscilla", [t21]),
        task(t23, "2.3", "Incorporate voice-over", "development", 0.5, "Priscilla", [t22]),
        task(t24, "2.4", "Functional review", "development", 1, "Priscilla", [t23],
             parallel_group=f"m{mod_idx}-dev-qa"),
        task(t25, "2.5", "Design review", "development", 1, "Priscilla", [t23],
             parallel_group=f"m{mod_idx}-dev-qa"),
        task(t26, "2.6", "Update", "development", 1, "Priscilla", [t23],
             parallel_group=f"m{mod_idx}-dev-qa"),
        task(t27, "2.7", "Submit for approval", "development", 1, "Priscilla", [t24, t25, t26]),
        task(t28, "2.8", "Approval", "development", 5, None, [t27]),

        task(t31, "3.1", "Save final files to dropbox", "upload", 1, "Priscilla", [t28],
             parallel_group=f"m{mod_idx}-upload"),
        task(t32, "3.2", "Upload to platform", "upload", 1, "Priscilla", [t28],
             parallel_group=f"m{mod_idx}-upload"),
        task(t33, "3.3", "Go live on platform", "upload", 1, "Priscilla", [t28],
             parallel_group=f"m{mod_idx}-upload"),
    ]

    return tasks, t15, t28


def main():
    all_tasks = []
    prev_approval_id = None
    prev_dev_approval_id = None

    for i, (name, subject, department) in enumerate(MODULES, start=1):
        new_tasks, approval_id, dev_approval_id = make_module(
            i, name, subject, department,
            prev_approval_id=prev_approval_id,
            prev_dev_approval_id=prev_dev_approval_id,
        )
        all_tasks.extend(new_tasks)
        prev_approval_id = approval_id
        prev_dev_approval_id = dev_approval_id

    payload = {
        "project_start": "2026-06-15",
        "gap_days": 0,
        "tasks": all_tasks,
    }

    out = Path(__file__).resolve().parent.parent / "data" / "tasks-training.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(all_tasks)} tasks ({N} modules × 15 steps) to {out}")


if __name__ == "__main__":
    main()
