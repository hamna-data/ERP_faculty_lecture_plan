{
    'name': 'Faculty Lecture Plan',
    'version': '1.0.0',
    'category': 'Education',
    'summary': 'Auto-generate lecture plans for faculty subjects and topics',
    'description': """
Faculty Lecture Plan
====================
    """,
    'author': 'Hamna Sakhawat',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/holiday_view.xml',
        'views/subject_view.xml',
        'views/topic_view.xml',
        'views/lecture_plan_view.xml',
        'views/lecture_plan_report.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
