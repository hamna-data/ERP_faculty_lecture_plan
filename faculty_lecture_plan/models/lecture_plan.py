from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime


class LecturePlan(models.Model):
    _name = "faculty.lecture.plan"
    _description = "Lecture Plan"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Lecture Plan Name", required=True, tracking=True)
    subject_id = fields.Many2one("faculty.subject", string="Subject", required=True, tracking=True)
    topic_ids = fields.Many2many("faculty.subject.topic", string="Topics", tracking=True)
    from_date = fields.Date(string="Start Date", required=True, tracking=True)
    to_date = fields.Date(string="End Date", required=True, tracking=True)

    # User input fields
    hours_per_day = fields.Float(string="Hours per Day", default=2.0, required=True, tracking=True, 
                                 help="Number of hours to teach daily")
    teaching_days = fields.Char(string="Teaching Days", default="Monday,Tuesday,Wednesday,Thursday,Friday", 
                               required=True, tracking=True, 
                               help="Enter the days when classes are scheduled (comma-separated, e.g., Monday,Tuesday,Friday)")
    
    # Computed fields for schedule
    total_days = fields.Integer(string="Total Days", compute="_compute_total_days", store=True)
    topics_per_day = fields.Integer(string="Topics Per Day", compute="_compute_topics_per_day", store=True)
    topics_per_chapter = fields.Integer(string="Topics Per Chapter", default=8)
    schedule_lines = fields.Text(string="Schedule", compute="_compute_schedule")

    @api.depends('from_date', 'to_date')
    def _compute_total_days(self):
        for record in self:
            if record.from_date and record.to_date:
                delta = record.to_date - record.from_date
                record.total_days = delta.days + 1
            else:
                record.total_days = 0

    @api.depends('hours_per_day')
    def _compute_topics_per_day(self):
        for record in self:
            if record.hours_per_day:
                # Each topic is fixed at 30 minutes, so calculate how many topics fit in the hours
                total_minutes = record.hours_per_day * 60
                record.topics_per_day = int(total_minutes / 30)  # 30 minutes per topic
            else:
                record.topics_per_day = 4  # Default 4 topics (2 hours)

    def _get_teaching_weekdays(self):
        """Parse teaching days string and return set of weekday numbers"""
        if not self.teaching_days:
            return set([0, 1, 2, 3, 4])  # Default to Monday-Friday
        
        # Map day names to weekday numbers
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        # Parse the teaching days string
        days = [day.strip().lower() for day in self.teaching_days.split(',')]
        weekdays = set()
        
        for day in days:
            if day in day_mapping:
                weekdays.add(day_mapping[day])
        
        return weekdays if weekdays else set([0, 1, 2, 3, 4])  # Default to Monday-Friday

    def _get_holiday_dates(self):
        """Get all active holiday dates"""
        holidays = self.env['faculty.holiday'].search([
            ('active', '=', True),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date)
        ])
        return set(holidays.mapped('date'))

    def _get_excluded_holidays(self):
        """Get holidays that fall on teaching days and will be excluded"""
        teaching_weekdays = self._get_teaching_weekdays()
        holidays = self.env['faculty.holiday'].search([
            ('active', '=', True),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date)
        ])
        
        excluded_holidays = []
        for holiday in holidays:
            if holiday.date.weekday() in teaching_weekdays:
                excluded_holidays.append(holiday)
        
        return excluded_holidays

    @api.depends('topic_ids', 'from_date', 'to_date', 'topics_per_day', 'teaching_days')
    def _compute_schedule(self):
        for record in self:
            if not record.topic_ids or not record.from_date or not record.to_date:
                record.schedule_lines = ""
                continue
            
            schedule = []
            topics = record.topic_ids
            current_date = record.from_date
            topic_index = 0
            day_number = 1
            
            # Get the teaching weekdays and holiday dates
            teaching_weekdays = record._get_teaching_weekdays()
            holiday_dates = record._get_holiday_dates()
            excluded_holidays = record._get_excluded_holidays()
            
            # Add information about excluded holidays at the beginning
            if excluded_holidays:
                schedule.append("EXCLUDED HOLIDAYS:")
                for holiday in excluded_holidays:
                    schedule.append(f"  - {holiday.name} ({holiday.date.strftime('%Y-%m-%d')} - {holiday.date.strftime('%A')})")
                schedule.append("")  # Empty line separator
            
            while topic_index < len(topics):
                # Check if current date is a teaching day and not a holiday
                if (current_date.weekday() in teaching_weekdays and 
                    current_date not in holiday_dates):
                    daily_topics = topics[topic_index:topic_index + record.topics_per_day]
                    topic_names = ", ".join(daily_topics.mapped('name'))
                    schedule.append(f"Day {day_number} ({current_date.strftime('%Y-%m-%d')} - {current_date.strftime('%A')}): {topic_names}")
                    
                    topic_index += record.topics_per_day
                    day_number += 1
                
                current_date += timedelta(days=1)
            
            record.schedule_lines = "\n".join(schedule)

    @api.onchange('subject_id')
    def _onchange_subject_id(self):
        """Automatically load all topics when subject is selected"""
        if self.subject_id:
            # Get all topics for the selected subject
            topics = self.env['faculty.subject.topic'].search([
                ('subject_id', '=', self.subject_id.id)
            ], order='sequence, id')
            self.topic_ids = topics
            # Return domain to filter topics by subject
            return {
                'domain': {
                    'topic_ids': [('subject_id', '=', self.subject_id.id)]
                }
            }
        else:
            self.topic_ids = False
            return {
                'domain': {
                    'topic_ids': [('id', '=', False)]
                }
            }

    @api.constrains('subject_id', 'topic_ids')
    def _check_topics_belong_to_subject(self):
        """Ensure all selected topics belong to the selected subject"""
        for record in self:
            if record.subject_id and record.topic_ids:
                invalid_topics = record.topic_ids.filtered(
                    lambda t: t.subject_id != record.subject_id
                )
                if invalid_topics:
                    raise ValidationError(_(
                        "All topics must belong to the selected subject '%s'. "
                        "Invalid topics: %s"
                    ) % (record.subject_id.name, ', '.join(invalid_topics.mapped('name'))))

    @api.constrains('hours_per_day')
    def _check_hours_per_day(self):
        """Ensure hours per day is reasonable"""
        for record in self:
            if record.hours_per_day <= 0:
                raise ValidationError(_("Hours per day must be greater than 0"))
            if record.hours_per_day > 12:
                raise ValidationError(_("Hours per day cannot exceed 12 hours"))

    def action_print_schedule(self):
        """Print the lecture plan schedule"""
        return self.env.ref('faculty_lecture_plan.action_report_lecture_plan').report_action(self)
