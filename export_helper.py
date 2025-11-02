import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import tempfile
import os


# =========================
# 📊 CSV Export Functions
# =========================

def export_statistics_csv(num_messages, words, num_media_messages, num_links):
    """Export basic statistics to CSV format"""
    data = {
        'Metric': ['Total Messages', 'Total Words', 'Total Media Shared', 'Total Links Shared'],
        'Value': [num_messages, words, num_media_messages, num_links]
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')


def export_dataframe_csv(df, columns=None):
    """Export any dataframe to CSV format"""
    if columns:
        df = df[columns]
    return df.to_csv(index=False).encode('utf-8')


def export_complete_analysis_csv(selected_user, df, stats_dict, timeline_df=None, 
                                  daily_timeline_df=None, common_words_df=None, 
                                  emoji_df=None, busy_users_df=None):
    """Export complete analysis to a single CSV with multiple sheets (requires Excel format)"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Statistics sheet
        stats_df = pd.DataFrame({
            'Metric': ['Total Messages', 'Total Words', 'Total Media Shared', 'Total Links Shared'],
            'Value': [stats_dict['messages'], stats_dict['words'], 
                     stats_dict['media'], stats_dict['links']]
        })
        stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        # Timeline sheets
        if timeline_df is not None and not timeline_df.empty:
            timeline_df.to_excel(writer, sheet_name='Monthly Timeline', index=False)
        
        if daily_timeline_df is not None and not daily_timeline_df.empty:
            daily_timeline_df.to_excel(writer, sheet_name='Daily Timeline', index=False)
        
        # Common words
        if common_words_df is not None and not common_words_df.empty:
            common_words_df.to_excel(writer, sheet_name='Common Words', index=False)
        
        # Emoji analysis
        if emoji_df is not None and not emoji_df.empty:
            emoji_df.to_excel(writer, sheet_name='Emoji Analysis', index=False)
        
        # Busy users (if Overall view)
        if busy_users_df is not None and not busy_users_df.empty:
            busy_users_df.to_excel(writer, sheet_name='Top Users', index=False)
    
    output.seek(0)
    return output.getvalue()


# =========================
# 📄 PDF Export Functions
# =========================

def export_statistics_pdf(selected_user, num_messages, words, num_media_messages, 
                          num_links, date_range=None):
    """Export basic statistics to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("WhatsApp Chat Analysis Report", title_style))
    story.append(Spacer(1, 12))
    
    # User info
    user_style = styles['Heading2']
    story.append(Paragraph(f"Analysis for: {selected_user}", user_style))
    
    if date_range:
        story.append(Paragraph(f"Date Range: {date_range}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Statistics table
    data = [
        ['Metric', 'Value'],
        ['Total Messages', f'{num_messages:,}'],
        ['Total Words', f'{words:,}'],
        ['Total Media Shared', f'{num_media_messages:,}'],
        ['Total Links Shared', f'{num_links:,}']
    ]
    
    table = Table(data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Spacer(1, 40))
    story.append(Paragraph("Generated by WhatsApp Chat Analyzer", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def export_complete_analysis_pdf(selected_user, stats_dict, date_range=None,
                                  common_words_df=None, emoji_df=None, 
                                  busy_users_df=None, charts=None):
    """Export complete analysis to PDF with tables and charts"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("WhatsApp Chat Analysis Report", title_style))
    story.append(Spacer(1, 12))
    
    # User info
    story.append(Paragraph(f"<b>Analysis for:</b> {selected_user}", styles['Heading2']))
    if date_range:
        story.append(Paragraph(f"<b>Date Range:</b> {date_range}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # === Statistics Section ===
    story.append(Paragraph("Key Statistics", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    stats_data = [
        ['Metric', 'Value'],
        ['Total Messages', f'{stats_dict.get("messages", 0):,}'],
        ['Total Words', f'{stats_dict.get("words", 0):,}'],
        ['Total Media Shared', f'{stats_dict.get("media", 0):,}'],
        ['Total Links Shared', f'{stats_dict.get("links", 0):,}']
    ]
    
    stats_table = Table(stats_data, colWidths=[3.5*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 30))
    
    # Initialize temp files list for cleanup
    temp_files = []
    
    # === Common Words Section ===
    if common_words_df is not None and not common_words_df.empty:
        story.append(Paragraph("Most Common Words (Top 10)", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        words_data = [['Word', 'Frequency']]
        for _, row in common_words_df.head(10).iterrows():
            words_data.append([str(row['Word']), str(row['Frequency'])])
        
        words_table = Table(words_data, colWidths=[3*inch, 2*inch])
        words_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ca02c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        story.append(words_table)
        story.append(Spacer(1, 30))
    
    # === Emoji Section ===
    if emoji_df is not None and not emoji_df.empty:
        story.append(Paragraph("Most Common Emojis", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Create emoji table as an image to preserve emoji rendering
        try:
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            import os
            import platform
            
            # Try to use a system font that supports emojis
            emoji_font = None
            try:
                system = platform.system()
                if system == 'Windows':
                    font_path = 'C:\\Windows\\Fonts\\seguiemj.ttf'
                elif system == 'Darwin':  # macOS
                    font_path = '/System/Library/Fonts/Apple Color Emoji.ttc'
                else:  # Linux
                    font_path = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
                
                if os.path.exists(font_path):
                    emoji_font = fm.FontProperties(fname=font_path)
            except:
                pass
            
            # Fallback to default if no emoji font found
            if emoji_font is None:
                emoji_font = fm.FontProperties()
            
            # Prepare data for table
            num_emojis = min(len(emoji_df), 10)  # Limit to top 10
            table_data = []
            
            for idx, row in emoji_df.head(10).iterrows():
                emoji_char = str(row['Emoji'])  # Use column name instead of iloc
                count = int(row['Count'])  # Use column name instead of iloc
                table_data.append([emoji_char, str(count)])
            
            # Create figure with table
            fig, ax = plt.subplots(figsize=(5, num_emojis * 0.5 + 0.8))
            ax.axis('tight')
            ax.axis('off')
            
            # Create the table
            table = ax.table(cellText=table_data,
                           colLabels=['Emoji', 'Count'],
                           cellLoc='center',
                           loc='center',
                           colWidths=[0.3, 0.7])
            
            # Style the table
            table.auto_set_font_size(False)
            
            # Style header
            for i in range(2):
                cell = table[(0, i)]
                cell.set_facecolor('#ff7f0e')
                cell.set_text_props(weight='bold', color='white', size=14)
                cell.set_height(0.08)
            
            # Style data rows
            for i in range(1, len(table_data) + 1):
                # Emoji column
                emoji_cell = table[(i, 0)]
                emoji_cell.set_text_props(fontproperties=emoji_font, size=24)
                emoji_cell.set_height(0.08)
                if i % 2 == 0:
                    emoji_cell.set_facecolor('#f0f0f0')
                else:
                    emoji_cell.set_facecolor('white')
                
                # Count column
                count_cell = table[(i, 1)]
                count_cell.set_text_props(size=12, weight='bold')
                count_cell.set_height(0.08)
                if i % 2 == 0:
                    count_cell.set_facecolor('#f0f0f0')
                else:
                    count_cell.set_facecolor('white')
            
            # Add border
            for key, cell in table.get_celld().items():
                cell.set_edgecolor('black')
                cell.set_linewidth(1)
            
            plt.tight_layout()
            
            # Save to temp file
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            tmp_path = tmp.name
            tmp.close()
            fig.savefig(tmp_path, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            # Add to PDF
            img = Image(tmp_path, width=4*inch, height=(num_emojis * 0.4 + 0.6)*inch)
            story.append(img)
            story.append(Spacer(1, 20))
            
            # Track temp file for cleanup
            temp_files.append(tmp_path)
            
        except Exception as e:
            print(f"Error creating emoji table image: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to text table without emojis
            emoji_data = [['Emoji #', 'Count']]
            for idx, row in emoji_df.iterrows():
                emoji_data.append([f"Emoji {idx+1}", str(row['Count'])])
            
            emoji_table = Table(emoji_data, colWidths=[3*inch, 2*inch])
            emoji_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff7f0e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
            ]))
            story.append(emoji_table)
        
        story.append(Spacer(1, 30))
    
    # === Top Users Section ===
    if busy_users_df is not None and not busy_users_df.empty:
        # Only add page break if content is getting long, otherwise just add space
        story.append(Spacer(1, 30))
        story.append(Paragraph("Top Contributors", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        users_data = [['Sender', 'Percentage (%)']]
        for _, row in busy_users_df.iterrows():
            users_data.append([str(row['Sender']), f"{row['Percentage']:.2f}"])
        
        users_table = Table(users_data, colWidths=[3*inch, 2*inch])
        users_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d62728')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        story.append(users_table)
        story.append(Spacer(1, 30))
    
    # === Add Charts if provided ===
    if charts and len(charts) > 0:
        story.append(PageBreak())
        story.append(Paragraph("📊 Visual Analysis & Charts", styles['Heading1']))
        story.append(Spacer(1, 20))
        
        chart_count = 0
        for chart_name, fig in charts.items():
            try:
                # Save figure to temporary file with high quality
                # Use delete=False to keep the file until after PDF is built
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp_path = tmp.name
                tmp.close()  # Close but don't delete
                
                # Save the figure
                fig.savefig(tmp_path, format='png', dpi=200, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                temp_files.append(tmp_path)  # Track for cleanup
                
                # Add chart title
                chart_title_style = ParagraphStyle(
                    'ChartTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=colors.HexColor('#1f77b4'),
                    spaceAfter=8
                )
                story.append(Paragraph(chart_name, chart_title_style))
                story.append(Spacer(1, 6))
                
                # Add chart image - adjust size based on chart type
                if 'Heatmap' in chart_name:
                    img = Image(tmp_path, width=6.5*inch, height=4*inch)
                elif 'Word Cloud' in chart_name:
                    img = Image(tmp_path, width=6*inch, height=4*inch)
                else:
                    img = Image(tmp_path, width=6.5*inch, height=3*inch)
                
                story.append(img)
                story.append(Spacer(1, 15))
                
                chart_count += 1
                # Add page break after every 2 charts to avoid crowding
                if chart_count % 2 == 0 and chart_count < len(charts):
                    story.append(PageBreak())
                
            except Exception as e:
                print(f"Error adding chart {chart_name}: {e}")
                import traceback
                traceback.print_exc()
                # Add error message in PDF
                error_style = styles['Normal']
                story.append(Paragraph(f"<i>Error generating chart: {chart_name}</i>", error_style))
                story.append(Spacer(1, 10))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Spacer(1, 40))
    story.append(Paragraph("Generated by WhatsApp Chat Analyzer", footer_style))
    
    # Build the PDF
    doc.build(story)
    
    # Clean up temp files AFTER PDF is built
    for tmp_path in temp_files:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception as e:
            print(f"Warning: Could not delete temp file {tmp_path}: {e}")
    
    buffer.seek(0)
    return buffer.getvalue()
