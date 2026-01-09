from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class FacultyHoliday(models.Model):
    _name = "faculty.holiday"
    _description = "Holiday"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc, name"

    name = fields.Char(string="Holiday Name", required=True, tracking=True)
    date = fields.Date(string="Date", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    year = fields.Integer(string="Year", compute="_compute_year", store=True)
    remarks = fields.Text(string="Remarks", tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    @api.depends('date')
    def _compute_year(self):
        """Compute year from date"""
        for record in self:
            if record.date:
                record.year = record.date.year
            else:
                record.year = 0

    @api.constrains('date')
    def _check_date(self):
        """Validate date is not in the past"""
        for record in self:
            if record.date and record.date < fields.Date.today():
                # Allow past dates but warn user
                pass

    @api.model
    def create(self, vals):
        """Set default name if not provided"""
        if not vals.get('name') and vals.get('date'):
            date_obj = fields.Date.from_string(vals['date'])
            vals['name'] = f"Holiday - {date_obj.strftime('%B %d, %Y')}"
        return super().create(vals)

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} ({record.date.strftime('%Y-%m-%d')})"
            result.append((record.id, name))
        return result
