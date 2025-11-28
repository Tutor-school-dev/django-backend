"""
Shared constants across the TutorSchool application
"""

# Class Level Constants - Used by both Teacher and Learner models
CLASS_LEVEL_CHOICES = [
    # I. SCHOOL LEVEL (Pre-Stream)
    ("Primary_School_Student", "Primary School Student (Classes 1-5)"),
    ("Secondary_School_Student", "Secondary School Student (Classes 6-10)"),
    
    # II. SENIOR SECONDARY STREAM (Classes 11-12)
    ("Senior_Secondary_Stream_Science", "Senior Secondary - Science Stream"),
    ("Senior_Secondary_Stream_Commerce", "Senior Secondary - Commerce Stream"),
    ("Senior_Secondary_Stream_Arts_or_Humanities", "Senior Secondary - Arts/Humanities Stream"),
    
    # III. UNDERGRADUATE (UG) LEVEL SPECIALIZATIONS
    ("UG_Science_Engineering_Core_(CSE/ECE/Mech/Civil)", "UG Science - Engineering Core (CSE/ECE/Mech/Civil)"),
    ("UG_Science_Pure_and_Applied_(Physics/Chem/Maths/Biotech)", "UG Science - Pure and Applied (Physics/Chem/Maths/Biotech)"),
    ("UG_Science_Medical_and_Health_Sciences_(MBBS/BDS)", "UG Science - Medical and Health Sciences (MBBS/BDS)"),
    ("UG_Commerce_Accounting_Taxation_and_Finance", "UG Commerce - Accounting, Taxation and Finance"),
    ("UG_Commerce_Business_Administration_and_Management_(BBA/BMS)", "UG Commerce - Business Administration and Management (BBA/BMS)"),
    ("UG_Arts_Humanities_and_Social_Sciences_(History/Psychology/Sociology)", "UG Arts - Humanities and Social Sciences (History/Psychology/Sociology)"),
    ("UG_Arts_Law_Integrated_(BA_LLB)", "UG Arts - Law Integrated (BA LLB)"),
    
    # IV. POSTGRADUATE (PG) LEVEL SPECIALIZATIONS
    ("PG_Technology_Advanced_Engineering_(AI/VLSI/Robotics)", "PG Technology - Advanced Engineering (AI/VLSI/Robotics)"),
    ("PG_Science_Advanced_Pure_Sciences_and_Research", "PG Science - Advanced Pure Sciences and Research"),
    ("PG_Management_MBA_Functional_(Finance/Marketing/HR)", "PG Management - MBA Functional (Finance/Marketing/HR)"),
    ("PG_Management_MBA_Sectoral_Analytics_and_Supply_Chain", "PG Management - MBA Sectoral Analytics and Supply Chain"),
    ("PG_Arts_Advanced_Policy_and_Specialized_Humanities", "PG Arts - Advanced Policy and Specialized Humanities"),
    ("PG_Law_LLM_Specialization_(Cyber_Law/IPR/Corporate)", "PG Law - LLM Specialization (Cyber Law/IPR/Corporate)"),
    
    # V. DOCTORAL (PhD) LEVEL RESEARCH AREAS
    ("Doctoral_Scholar_STEM_Frontier_Technology_and_Basic_Science_Research", "Doctoral Scholar - STEM Frontier Technology and Basic Science Research"),
    ("Doctoral_Scholar_Management_Organizational_Behavior_and_Strategy_Research", "Doctoral Scholar - Management, Organizational Behavior and Strategy Research"),
    ("Doctoral_Scholar_Arts_Law_Theoretical_and_Policy_Research", "Doctoral Scholar - Arts/Law Theoretical and Policy Research"),
]

# Teaching/Learning Mode Constants
TEACHING_MODE_CHOICES = [
    ('ONLINE', 'Online'),
    ('OFFLINE', 'Offline'),
    ('BOTH', 'Both'),
]

PREFERRED_MODE_CHOICES = [
    ('Online', 'Online'),
    ('Offline', 'Offline'),
    ('Both', 'Both'),
]
