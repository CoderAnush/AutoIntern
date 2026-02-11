"""
Email service for sending emails via SMTP.
Supports both HTML and plain text versions.
"""

import os
import asyncio
import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP with retry logic."""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        sender_email: str = None,
        sender_password: str = None,
    ):
        """
        Initialize email service with SMTP configuration.

        Args:
            smtp_host: SMTP server hostname (default: from env)
            smtp_port: SMTP server port (default: from env)
            sender_email: Email address to send from (default: from env)
            sender_password: SMTP password/token (default: from env)
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", "noreply@autointern.com")
        self.sender_password = sender_password or os.getenv("SENDER_PASSWORD", "")

        if not self.sender_password:
            logger.warning("SENDER_PASSWORD not configured - emails will not be sent")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: str,
        max_retries: int = 3,
    ) -> bool:
        """
        Send email with both HTML and plain text versions.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text: Plain text email body (fallback)
            max_retries: Maximum retry attempts

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.sender_password:
            logger.error("Cannot send email: SENDER_PASSWORD not configured")
            return False

        # Validate email format
        if not self._is_valid_email(to_email):
            logger.error(f"Invalid email address: {to_email}")
            return False

        # Create MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = to_email

        # Attach plain text and HTML versions
        part1 = MIMEText(plain_text, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Send with retries
        for attempt in range(max_retries):
            try:
                async with aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=True,
                ) as smtp:
                    await smtp.login(self.sender_email, self.sender_password)
                    await smtp.send_message(message)

                logger.info(f"Email sent successfully to {to_email}")
                return True

            except Exception as e:
                logger.error(f"Failed to send email (attempt {attempt + 1}/{max_retries}): {str(e)}")

                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to send email to {to_email} after {max_retries} attempts")
                    return False

        return False

    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """
        Send welcome email to new user.

        Args:
            user_email: User's email address
            user_name: User's display name

        Returns:
            True if sent successfully
        """
        subject = "Welcome to AutoIntern!"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2c3e50;">Welcome to AutoIntern, {user_name}!</h1>

                    <p>Your account has been created successfully. You're now ready to discover your perfect job matches.</p>

                    <h2 style="color: #4CAF50;">Get Started in 3 Steps:</h2>
                    <ol style="line-height: 1.8;">
                        <li><strong>Upload your resume</strong> (PDF, DOCX, or TXT format)</li>
                        <li><strong>Search for jobs</strong> by keyword or location</li>
                        <li><strong>Let our AI recommend</strong> the perfect job matches for you</li>
                    </ol>

                    <p style="margin-top: 30px;">
                        <a href="http://localhost:3000/login"
                           style="display: inline-block; padding: 12px 30px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
                            Go to Dashboard
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="color: #666; font-size: 12px;">
                        Best regards,<br>
                        <strong>AutoIntern Team</strong><br>
                        <em>Your AI-powered job recommendation platform</em>
                    </p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
Welcome to AutoIntern, {user_name}!

Your account has been created successfully. You're now ready to discover your perfect job matches.

Get Started in 3 Steps:
1. Upload your resume (PDF, DOCX, or TXT format)
2. Search for jobs by keyword or location
3. Let our AI recommend the perfect job matches for you

Go to Dashboard: http://localhost:3000/login

Best regards,
AutoIntern Team
Your AI-powered job recommendation platform
        """

        return await self.send_email(user_email, subject, html_content, plain_text)

    async def send_resume_upload_confirmation(
        self, user_email: str, resume_name: str, skills: List[str]
    ) -> bool:
        """
        Send resume upload confirmation with detected skills.

        Args:
            user_email: User's email address
            resume_name: Name of uploaded resume file
            skills: List of detected skills

        Returns:
            True if sent successfully
        """
        subject = f"Resume Upload Confirmed: {resume_name}"

        skills_list = "<ul>" + "".join(f"<li>{skill}</li>" for skill in skills) + "</ul>"
        if not skills:
            skills_list = "<p><em>No skills detected. Try uploading with more detailed content.</em></p>"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2c3e50;">Resume Upload Confirmed!</h1>

                    <p>Your resume <strong>{resume_name}</strong> has been successfully uploaded and processed.</p>

                    <h2 style="color: #4CAF50;">Detected Skills:</h2>
                    {skills_list}

                    <p style="margin-top: 30px; padding: 15px; background-color: #f0f0f0; border-radius: 4px;">
                        <strong>Next Step:</strong> View job recommendations based on your skills and experience.
                    </p>

                    <p>
                        <a href="http://localhost:3000/dashboard?tab=recommendations"
                           style="display: inline-block; padding: 12px 30px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
                            View Job Recommendations
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="color: #666; font-size: 12px;">
                        AutoIntern Team<br>
                        <em>Your AI-powered job recommendation platform</em>
                    </p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
Resume Upload Confirmed!

Your resume {resume_name} has been successfully uploaded and processed.

Detected Skills:
{chr(10).join(f"• {skill}" for skill in skills) if skills else "No skills detected. Try uploading with more detailed content."}

Next Step: View job recommendations based on your skills and experience.

View Job Recommendations: http://localhost:3000/dashboard?tab=recommendations

AutoIntern Team
Your AI-powered job recommendation platform
        """

        return await self.send_email(user_email, subject, html_content, plain_text)

    async def send_job_alert_email(
        self, user_email: str, resume_name: str, match_count: int, top_jobs: List[dict]
    ) -> bool:
        """
        Send job match alert email with top recommended jobs.

        Args:
            user_email: User's email address
            resume_name: Name of the resume being matched
            match_count: Total number of matches found
            top_jobs: List of top job recommendations (max 5)

        Returns:
            True if sent successfully
        """
        subject = f"🎯 {match_count} New Job Matches Found!"

        # Build jobs table
        jobs_html = ""
        for job in top_jobs[:5]:
            similarity = int(job.get("similarity_score", 0) * 100)
            jobs_html += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 12px; text-align: left;"><strong>{job.get("job_title", "Unknown")}</strong></td>
                <td style="padding: 12px; text-align: left;">{job.get("company", "Unknown")}</td>
                <td style="padding: 12px; text-align: left;">{job.get("location", "Remote")}</td>
                <td style="padding: 12px; text-align: center;">
                    <span style="background-color: {'#4CAF50' if similarity >= 70 else '#FF9800'}; color: white; padding: 4px 8px; border-radius: 3px;">
                        {similarity}%
                    </span>
                </td>
            </tr>
            """

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2c3e50;">🎯 New Job Matches Found!</h1>

                    <p>Hi there,</p>

                    <p>We found <strong>{match_count} new jobs</strong> matching your resume <strong>{resume_name}</strong>!</p>

                    <h2 style="color: #4CAF50;">Top Matches:</h2>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f0f0f0;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Job Title</th>
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Company</th>
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Location</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Match</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs_html}
                        </tbody>
                    </table>

                    <p style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:3000/dashboard?tab=jobs"
                           style="display: inline-block; padding: 12px 30px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
                            View All Matches on Dashboard
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="color: #666; font-size: 12px;">
                        AutoIntern Team<br>
                        <em>Your AI-powered job recommendation platform</em>
                    </p>
                </div>
            </body>
        </html>
        """

        jobs_text = "\n".join(
            f"• {job.get('job_title', 'Unknown')} at {job.get('company', 'Unknown')} "
            f"({job.get('location', 'Remote')}) - {int(job.get('similarity_score', 0) * 100)}% match"
            for job in top_jobs[:5]
        )

        plain_text = f"""
🎯 New Job Matches Found!

Hi there,

We found {match_count} new jobs matching your resume {resume_name}!

Top Matches:

{jobs_text}

View All Matches on Dashboard: http://localhost:3000/dashboard?tab=jobs

AutoIntern Team
Your AI-powered job recommendation platform
        """

        return await self.send_email(user_email, subject, html_content, plain_text)

    async def send_password_change_notification(
        self, user_email: str, user_name: str = "User"
    ) -> bool:
        """
        Send security notification when password is changed.

        Args:
            user_email: User's email address
            user_name: User's display name

        Returns:
            True if sent successfully
        """
        subject = "🔒 Your Password Was Changed"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #d32f2f;">🔒 Password Changed</h1>

                    <p>Hi {user_name},</p>

                    <p>Your AutoIntern account password was successfully changed.</p>

                    <div style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Important:</strong> If you did not make this change, please reset your password immediately.</p>
                    </div>

                    <p style="margin-top: 30px;">
                        <a href="http://localhost:3000/dashboard?tab=settings"
                           style="display: inline-block; padding: 12px 30px; background-color: #d32f2f; color: white; text-decoration: none; border-radius: 4px;">
                            Go to Account Settings
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="color: #666; font-size: 12px;">
                        <strong>Security Note:</strong> This email was sent for security purposes. If you believe your account is compromised, please contact our support team immediately.
                    </p>

                    <p style="color: #666; font-size: 12px;">
                        AutoIntern Security Team<br>
                        <em>Your AI-powered job recommendation platform</em>
                    </p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
🔒 Password Changed

Hi {user_name},

Your AutoIntern account password was successfully changed.

⚠️ Important: If you did not make this change, please reset your password immediately.

Go to Account Settings: http://localhost:3000/dashboard?tab=settings

Security Note: This email was sent for security purposes. If you believe your account is compromised, please contact our support team immediately.

AutoIntern Security Team
Your AI-powered job recommendation platform
        """

        return await self.send_email(user_email, subject, html_content, plain_text)

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Basic email validation (check for @ and domain).

        Args:
            email: Email address to validate

        Returns:
            True if email looks valid
        """
        if not email or "@" not in email:
            return False

        parts = email.split("@")
        if len(parts) != 2:
            return False

        local_part, domain = parts

        if not local_part or not domain:
            return False

        if "." not in domain:
            return False

        return True
