from odoo import models, fields

class FacultySubjectTopic(models.Model):
    _name = 'faculty.subject.topic'
    _description = 'Faculty Subject Topic'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Topic Title", required=True, tracking=True)
    duration = fields.Integer(
        string="Duration (Minutes)",
        default=30,
        readonly=True,
        tracking=True
    )
    sequence = fields.Integer(string="Sequence", default=1, tracking=True)

    subject_id = fields.Many2one(
        'faculty.subject',
        string="Subject",
        required=True,
        ondelete="cascade",
        tracking=True
    )
