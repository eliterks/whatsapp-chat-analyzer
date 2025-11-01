import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import datetime


# =========================
# 📄 CSV Export Functions
# =========================

def generate_csv_summary(selected_user, df, stats, monthly_timeline, daily_timeline, 
                        busy_day, busy_month, most_common_df, emoji_df, user_heatmap):
    """
    Generate a comprehensive CSV export with all analysis data.
    Returns a BytesIO object containing the CSV data.
    """
    output = BytesIO()
    
    # Create a writer object
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Summary Statistics
        summary_df = pd.DataFrame({
            'Metric': ['Total Messages', 'Total Words', 'Media Messages', 'Links Shared'],
            'Value': [stats[0], stats[1], stats[2], stats[3]]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Monthly Timeline
        if not monthly_timeline.empty:
            monthly_timeline.to_excel(writer, sheet_name='Monthly Timeline', index=False)
        
        # Daily Timeline
        if not daily_timeline.empty:
            daily_timeline.to_excel(writer, sheet_name='Daily Timeline', index=False)
        
        # Most Active Days
        if not busy_day.empty:
            busy_day.to_frame('Message Count').to_excel(writer, sheet_name='Active Days')
        
        # Most Active Months
        if not busy_month.empty:
            busy_month.to_frame('Message Count').to_excel(writer, sheet_name='Active Months')
        
        # Most Common Words
        if not most_common_df.empty:
            most_common_df.to_excel(writer, sheet_name='Common Words', index=False)
        
        # Emoji Analysis
        if not emoji_df.empty:
            emoji_df.to_excel(writer, sheet_name='Emojis', index=False)
        
        # Activity Heatmap
        if not user_heatmap.empty:
            user_heatmap.to_excel(writer, sheet_name='Activity Heatmap')
    
    output.seek(0)
    return output


def generate_simple_csv(selected_user, df, stats):
    """
    Generate a simple CSV with basic statistics only.
    Returns a BytesIO object containing the CSV data.
    """
    output = BytesIO()
    
    summary_df = pd.DataFrame({
        'User': [selected_user],
        'Total Messages': [stats[0]],
        'Total Words': [stats[1]],
        'Media Messages': [stats[2]],
        'Links Shared': [stats[3]]
    })
    
    summary_df.to_csv(output, index=False)
    output.seek(0)
    return output


# =========================
# 📊 PDF Export Functions
# =========================

def fig_to_image(fig, width=6*inch, height=4*inch):
    """
    Convert a matplotlib figure to a ReportLab Image object.
    """
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
    img_buffer.seek(0)
    img = Image(img_buffer, width=width, height=height)
    plt.close(fig)
    return img


def generate_pdf_report(selected_user, df, stats, monthly_timeline, daily_timeline,
                       busy_day, busy_month, most_common_df, emoji_df, user_heatmap,
                       top_users_data=None):
    """
    Generate a comprehensive PDF report with all analysis data and charts.
    Returns a BytesIO object containing the PDF data.
    """
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4,
                          topMargin=0.5*inch, bottomMargin=0.5*inch,
                          leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2ca02c'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph(f"WhatsApp Chat Analysis Report", title_style)
    elements.append(title)
    
    # Report metadata
    report_date = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")
    metadata = Paragraph(f"<b>User:</b> {selected_user}<br/><b>Generated:</b> {report_date}", 
                        styles['Normal'])
    elements.append(metadata)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary Statistics
    elements.append(Paragraph("Summary Statistics", heading_style))
    
    stats_data = [
        ['Metric', 'Value'],
        ['Total Messages', f"{stats[0]:,}"],
        ['Total Words', f"{stats[1]:,}"],
        ['Media Messages', f"{stats[2]:,}"],
        ['Links Shared', f"{stats[3]:,}"]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Monthly Timeline Chart
    if not monthly_timeline.empty:
        elements.append(Paragraph("Monthly Timeline", heading_style))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(monthly_timeline['time'], monthly_timeline['Message'], color='green', marker='o')
        ax.set_xlabel('Time')
        ax.set_ylabel('Messages')
        ax.set_title('Monthly Message Timeline')
        plt.xticks(rotation=45)
        plt.tight_layout()
        elements.append(fig_to_image(fig))
        elements.append(Spacer(1, 0.2*inch))
    
    # Activity Map - Most Active Days
    if not busy_day.empty:
        elements.append(Paragraph("Most Active Days", heading_style))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(busy_day.index, busy_day.values, color='orange')
        ax.set_xlabel('Day of Week')
        ax.set_ylabel('Message Count')
        ax.set_title('Most Active Days')
        plt.xticks(rotation=45)
        plt.tight_layout()
        elements.append(fig_to_image(fig))
        elements.append(Spacer(1, 0.2*inch))
    
    # Page Break
    elements.append(PageBreak())
    
    # Most Active Months
    if not busy_month.empty:
        elements.append(Paragraph("Most Active Months", heading_style))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(busy_month.index, busy_month.values, color='purple')
        ax.set_xlabel('Month')
        ax.set_ylabel('Message Count')
        ax.set_title('Most Active Months')
        plt.xticks(rotation=45)
        plt.tight_layout()
        elements.append(fig_to_image(fig))
        elements.append(Spacer(1, 0.2*inch))
    
    # Activity Heatmap
    if not user_heatmap.empty and not user_heatmap.isnull().all().all():
        elements.append(Paragraph("Activity Heatmap", heading_style))
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(user_heatmap, ax=ax, cmap='YlOrRd')
        ax.set_title('Weekly Activity Heatmap')
        plt.tight_layout()
        elements.append(fig_to_image(fig, width=6.5*inch, height=4*inch))
        elements.append(Spacer(1, 0.2*inch))
    
    # Top Users (if Overall analysis)
    if top_users_data is not None:
        elements.append(PageBreak())
        elements.append(Paragraph("Top 5 Most Active Users", heading_style))
        
        top_users_x, top_users_df = top_users_data
        
        # Chart
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(top_users_x.index, top_users_x.values, color='green')
        ax.set_xlabel('User')
        ax.set_ylabel('Message Count')
        ax.set_title('Top 5 Most Active Users')
        plt.xticks(rotation=45)
        plt.tight_layout()
        elements.append(fig_to_image(fig))
        elements.append(Spacer(1, 0.2*inch))
        
        # Table
        if not top_users_df.empty:
            elements.append(Paragraph("User Contribution Percentage", heading_style))
            table_data = [['Sender', 'Percentage (%)']]
            for _, row in top_users_df.head(10).iterrows():
                table_data.append([str(row['Sender']), f"{row['Percentage']:.2f}%"])
            
            user_table = Table(table_data, colWidths=[3*inch, 2*inch])
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(user_table)
            elements.append(Spacer(1, 0.2*inch))
    
    # Most Common Words
    if not most_common_df.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("Most Common Words", heading_style))
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(most_common_df['Word'], most_common_df['Frequency'], color='steelblue')
        ax.set_xlabel('Frequency')
        ax.set_ylabel('Word')
        ax.set_title('Top 20 Most Common Words')
        plt.tight_layout()
        elements.append(fig_to_image(fig))
        elements.append(Spacer(1, 0.2*inch))
    
    # Emoji Analysis
    if not emoji_df.empty:
        elements.append(Paragraph("Most Common Emojis", heading_style))
        
        # Create emoji table
        emoji_table_data = [['Emoji', 'Count']]
        for _, row in emoji_df.iterrows():
            emoji_table_data.append([str(row['Emoji']), str(row['Count'])])
        
        emoji_table = Table(emoji_table_data, colWidths=[2*inch, 2*inch])
        emoji_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(emoji_table)
    
    # Build PDF
    doc.build(elements)
    output.seek(0)
    return output
