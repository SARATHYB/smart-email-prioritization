# ingestion/mock_generator.py
"""
Mock Email Generator for Smart Email Prioritization.
Generates realistic academic, placement, internship, and scholarship emails
specifically for sarathybhas@gmail.com with dynamic temporal deadlines.
"""

from datetime import datetime, timedelta
from typing import List
from core.models import RawEmail
from ingestion.base import EmailIngestionProvider
from core.config import settings


class MockEmailGenerator(EmailIngestionProvider):
    def __init__(self, target_email: str = None):
        self.target_email = target_email or settings.mock_target_email

    def fetch_emails(self, max_count: int = 50) -> List[RawEmail]:
        now = datetime.now()

        # Dynamic target dates relative to current execution time
        d_14h = now + timedelta(hours=14)
        d_26h = now + timedelta(hours=26)
        d_3d  = now + timedelta(days=3, hours=4)
        d_5d  = now + timedelta(days=5, hours=9)
        d_8d  = now + timedelta(days=8, hours=12)
        d_14d = now + timedelta(days=14, hours=18)
        d_exp = now - timedelta(days=2)  # Expired deadline

        mock_templates = [
            {
                "id": "mock_placement_amazon_001",
                "subject": "🔥 URGENT: Amazon Campus Recruitment 2026 - SDE 1 Application Window Closing",
                "sender": "Amazon University Talent Acquisition <talent@amazon.com>",
                "body": (
                    f"Dear Candidate,\n\n"
                    f"This is an urgent reminder that the registration link for Amazon SDE-1 Campus Hiring "
                    f"is closing soon. CTC offered: 28 LPA. Eligible branches: CSE, IT, Data Engineering.\n\n"
                    f"Online Assessment (OA) details will be sent immediately upon registration.\n"
                    f"Last date to apply is {d_14h.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
                    f"Applications submitted after the deadline will NOT be entertained.\n\n"
                    f"Regards,\nAmazon Campus Recruitment Team"
                ),
                "timestamp": (now - timedelta(hours=4)).isoformat(),
            },
            {
                "id": "mock_internship_google_002",
                "subject": "Google Summer of Code (GSoC) 2027: Contributor Proposal Submission Open",
                "sender": "Google Open Source Programs <gsoc-support@google.com>",
                "body": (
                    f"Hello Open Source Enthusiast,\n\n"
                    f"Submissions for Google Summer of Code project proposals are now officially open. "
                    f"Mentoring organizations have published their project idea lists covering AI, systems, and web technologies.\n\n"
                    f"Submit your proposal before the deadline: {d_3d.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
                    f"Ensure you discuss your draft with community mentors before final submission.\n\n"
                    f"Best regards,\nThe Google Open Source Programs Team"
                ),
                "timestamp": (now - timedelta(hours=12)).isoformat(),
            },
            {
                "id": "mock_exam_cat2_003",
                "subject": "VIT University: CAT-2 Mid-Term Examination Schedule & Hall Ticket Release",
                "sender": "Controller of Examinations <coe@vit.ac.in>",
                "body": (
                    f"Dear Student,\n\n"
                    f"The Continuous Assessment Test 2 (CAT-2) for Winter Semester 2025-26 has been scheduled. "
                    f"Hall tickets will be verified at the examination hall entrance.\n\n"
                    f"Exam starts on {d_5d.strftime('%B %d, %Y at 09:30 AM')}.\n\n"
                    f"Please review your slot timetable and seating arrangement on VTOP before the examination date.\n\n"
                    f"Controller of Examinations\nVIT University"
                ),
                "timestamp": (now - timedelta(days=1)).isoformat(),
            },
            {
                "id": "mock_mentorship_microsoft_004",
                "subject": "Microsoft Azure Student AI Mentorship Cohort - Final Shortlist & Confirmation",
                "sender": "Microsoft Student Programs <msstudent@microsoft.com>",
                "body": (
                    f"Congratulations Sarathy!\n\n"
                    f"You have been shortlisted for the Microsoft Azure Cloud & AI Mentorship program. "
                    f"You will be paired with Senior Microsoft Engineers for 8 weeks.\n\n"
                    f"To accept and secure your cohort seat, register by {d_26h.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
                    f"Failure to confirm will result in the slot passing to the waitlisted candidate.\n\n"
                    f"Warm regards,\nMicrosoft Student Developer Relations"
                ),
                "timestamp": (now - timedelta(hours=8)).isoformat(),
            },
            {
                "id": "mock_scholarship_merit_005",
                "subject": "National Post-Graduate Merit Scholarship 2026: Application Portal Open",
                "sender": "Ministry of Education Financial Aid <scholarships@gov.in>",
                "body": (
                    f"Notice to all eligible Data Science and Engineering post-graduate students:\n\n"
                    f"The Central Sector Merit Scholarship awards Rs. 25,000 per month for meritorious students with CGPA >= 8.5.\n\n"
                    f"Interested students must submit certified transcripts and income documentation.\n"
                    f"The closing date is {d_14d.strftime('%B %d, %Y')}.\n\n"
                    f"Incomplete forms will be automatically rejected.\n\n"
                    f"National Scholarship Portal Helpdesk"
                ),
                "timestamp": (now - timedelta(days=2)).isoformat(),
            },
            {
                "id": "mock_event_hackathon_006",
                "subject": "Smart India Hackathon 2026 - Internal University Round Team Registration",
                "sender": "Student Technical Council <council@vit.ac.in>",
                "body": (
                    f"Hey Hackers!\n\n"
                    f"Registrations are now live for the Smart India Hackathon (SIH 2026) internal college shortlist. "
                    f"Top 10 teams will represent the university at the grand finale.\n\n"
                    f"Team size: 6 members (minimum 1 female member mandatory).\n"
                    f"Last date to register is {d_8d.strftime('%B %d, %Y at 11:59 PM')}.\n\n"
                    f"Cash prizes: 1st Place Rs. 75,000 | 2nd Place Rs. 50,000.\n\n"
                    f"Happy Hacking,\nTechnical Activities Committee"
                ),
                "timestamp": (now - timedelta(days=1, hours=5)).isoformat(),
            },
            {
                "id": "mock_expired_cisco_007",
                "subject": "Cisco Cyber Challenge 2026: Round 1 Project Code Submission",
                "sender": "Cisco Competitions <cyberchallenge@cisco.com>",
                "body": (
                    f"Dear Participant,\n\n"
                    f"Thank you for attending the Cisco Cyber Challenge. "
                    f"Your GitHub repository URL had to be submitted for evaluation.\n\n"
                    f"The submission deadline was {d_exp.strftime('%B %d, %Y at 11:59 PM')}.\n\n"
                    f"This competition round is now officially closed.\n\n"
                    f"Cisco University Programs"
                ),
                "timestamp": (now - timedelta(days=3)).isoformat(),
            },
            {
                "id": "mock_general_welfare_008",
                "subject": "Dean's Circular: Weekend Campus Sustainability & Green Mobility Drive",
                "sender": "Office of Student Welfare <dean.sw@vit.ac.in>",
                "body": (
                    f"Dear Students and Faculty,\n\n"
                    f"As part of our commitment to sustainable campus living, the university is launching "
                    f"a dedicated bicycle-sharing network across the residential blocks and academic buildings.\n\n"
                    f"Stations are active starting this Saturday morning. Helmet usage is strongly recommended. "
                    f"No registration required; access using student ID cards.\n\n"
                    f"Warm regards,\nOffice of the Dean, Student Welfare"
                ),
                "timestamp": (now - timedelta(days=2)).isoformat(),
            }
        ]

        raw_emails = []
        for t in mock_templates[:max_count]:
            raw_emails.append(RawEmail(
                id=t["id"],
                subject=t["subject"],
                sender=t["sender"],
                body=t["body"],
                timestamp=t["timestamp"],
                recipient=self.target_email
            ))

        return raw_emails
