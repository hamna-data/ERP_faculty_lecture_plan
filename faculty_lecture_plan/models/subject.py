from odoo import models, fields

class FacultySubject(models.Model):
    _name = 'faculty.subject'
    _description = 'Faculty Subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Subject Name", required=True, tracking=True)
    code = fields.Char(string="Subject Code", tracking=True)
    description = fields.Text(string="Description", tracking=True)

    topic_ids = fields.One2many(
        'faculty.subject.topic',
        'subject_id',
        string="Topics"
    )
