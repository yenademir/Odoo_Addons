{
    'name': 'Scrum Project',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Scrum management for projects',
        'depends': [
        'analytic',
        'base_setup',
        'mail',
        'portal',
        'rating',
        'resource',
        'web',
        'web_tour',
        'digest',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/scrum_view.xml',
    ],
    'css': ['static/src/css/custom.css'],

    'installable': True,
    'application': True,
}
