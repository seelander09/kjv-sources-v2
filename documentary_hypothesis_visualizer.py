#!/usr/bin/env python3
"""
Documentary Hypothesis Visual Analysis Tool
==========================================

Creates interactive visualizations for Documentary Hypothesis research
including source distribution charts, theological theme analysis, and
comparative visualizations.
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, List, Any, Optional
import base64
from io import BytesIO
from qdrant_client import QdrantClient

class DocumentaryHypothesisVisualizer:
    """Creates visualizations for Documentary Hypothesis research"""
    
    def __init__(self):
        self.qdrant_client = None
        self.colors = {
            'J': '#000088',  # Navy Blue
            'E': '#008888',  # Teal  
            'P': '#888800',  # Olive Yellow
            'D': '#000000',  # Black
            'R': '#880000'   # Maroon Red
        }
        
    def setup_qdrant_connection(self):
        """Connect to Qdrant database"""
        try:
            # Use local Qdrant instance
            qdrant_path = Path("qdrant_data")
            self.qdrant_client = QdrantClient(path=str(qdrant_path))
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            return False
    
    def get_source_distribution_data(self) -> Dict[str, Any]:
        """Get source distribution data for visualization"""
        if not self.qdrant_client:
            return {}
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
            source_data = {}
            
            for book in books:
                book_data = {}
                for source in ['J', 'E', 'P', 'D', 'R']:
                    # Search for verses with specific source
                    result = self.qdrant_client.search(
                        collection_name="kjv_sources",
                        query_vector=[0] * 384,  # Dummy vector for filtering only
                        query_filter=Filter(
                            must=[
                                FieldCondition(key="book", match=MatchValue(value=book)),
                                FieldCondition(key="sources", match=MatchValue(value=source))
                            ]
                        ),
                        limit=1000  # Get all matching results
                    )
                    book_data[source] = len(result)
                source_data[book] = book_data
            
            return source_data
            
        except Exception as e:
            print(f"Error getting source distribution: {e}")
            return {}
    
    def create_source_distribution_chart(self) -> str:
        """Create interactive source distribution chart"""
        data = self.get_source_distribution_data()
        if not data:
            return "No data available"
        
        # Prepare data for plotting
        books = list(data.keys())
        sources = ['J', 'E', 'P', 'D', 'R']
        
        fig = go.Figure()
        
        for source in sources:
            values = [data[book].get(source, 0) for book in books]
            fig.add_trace(go.Bar(
                name=source,
                x=books,
                y=values,
                marker_color=self.colors[source],
                text=values,
                textposition='auto'
            ))
        
        fig.update_layout(
            title="Documentary Hypothesis Source Distribution Across Biblical Books",
            xaxis_title="Biblical Books",
            yaxis_title="Number of Verses",
            barmode='stack',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def create_source_percentage_chart(self) -> str:
        """Create pie chart showing source percentages"""
        data = self.get_source_distribution_data()
        if not data:
            return "No data available"
        
        # Calculate total verses per source
        source_totals = {'J': 0, 'E': 0, 'P': 0, 'D': 0, 'R': 0}
        
        for book_data in data.values():
            for source, count in book_data.items():
                source_totals[source] += count
        
        # Create pie chart
        labels = list(source_totals.keys())
        values = list(source_totals.values())
        colors = [self.colors[label] for label in labels]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='label+percent+value',
            textfont_size=12
        )])
        
        fig.update_layout(
            title="Overall Source Distribution in Pentateuch",
            height=500,
            showlegend=True
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def create_theological_theme_analysis(self, theme: str) -> str:
        """Create visualization for theological theme analysis"""
        if not self.weaviate_client:
            return "No database connection"
        
        try:
            collection = self.weaviate_client.collections.get("BiblicalVerse")
            
            # Search for theme across sources
            result = collection.query.fetch_objects(
                where={
                    "path": ["text"],
                    "operator": "Like",
                    "valueText": f"*{theme}*"
                },
                limit=100
            )
            
            # Analyze by source
            source_counts = {'J': 0, 'E': 0, 'P': 0, 'D': 0, 'R': 0}
            book_counts = {}
            
            for obj in result.objects:
                sources = obj.properties.get('sources', '')
                book = obj.properties.get('book', '')
                
                for source in sources:
                    if source in source_counts:
                        source_counts[source] += 1
                
                if book not in book_counts:
                    book_counts[book] = 0
                book_counts[book] += 1
            
            # Create subplot with two charts
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f'"{theme}" Theme by Source', f'"{theme}" Theme by Book'),
                specs=[[{"type": "pie"}, {"type": "bar"}]]
            )
            
            # Pie chart for sources
            fig.add_trace(
                go.Pie(
                    labels=list(source_counts.keys()),
                    values=list(source_counts.values()),
                    marker_colors=[self.colors[label] for label in source_counts.keys()],
                    name="Sources"
                ),
                row=1, col=1
            )
            
            # Bar chart for books
            fig.add_trace(
                go.Bar(
                    x=list(book_counts.keys()),
                    y=list(book_counts.values()),
                    name="Books",
                    marker_color='lightblue'
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title=f"Theological Theme Analysis: '{theme}'",
                height=500,
                showlegend=False
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            return f"Error creating theme analysis: {e}"
    
    def create_parallel_passage_network(self, theme: str) -> str:
        """Create network visualization for parallel passages"""
        if not self.weaviate_client:
            return "No database connection"
        
        try:
            collection = self.weaviate_client.collections.get("BiblicalVerse")
            
            # Find parallel passages
            result = collection.query.fetch_objects(
                where={
                    "path": ["text"],
                    "operator": "Like",
                    "valueText": f"*{theme}*"
                },
                limit=50
            )
            
            # Create network data
            nodes = []
            edges = []
            node_id = 0
            
            for obj in result.objects:
                reference = obj.properties.get('canonical_reference', '')
                sources = obj.properties.get('sources', '')
                book = obj.properties.get('book', '')
                
                # Add node for each passage
                nodes.append({
                    'id': node_id,
                    'label': reference,
                    'group': sources,
                    'title': f"{reference}<br>Source: {sources}<br>Book: {book}"
                })
                
                # Add edges between passages from same source
                for other_id, other_obj in enumerate(result.objects):
                    if other_id != node_id:
                        other_sources = other_obj.properties.get('sources', '')
                        if sources and other_sources and sources in other_sources:
                            edges.append({
                                'from': node_id,
                                'to': other_id,
                                'color': {'color': self.colors.get(sources[0], '#888888')}
                            })
                
                node_id += 1
            
            # Create network visualization using Plotly
            fig = go.Figure()
            
            # Add edges
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[], y=[],
                    mode='lines',
                    line=dict(color=edge['color']['color'], width=1),
                    hoverinfo='none',
                    showlegend=False
                ))
            
            # Add nodes
            for node in nodes:
                fig.add_trace(go.Scatter(
                    x=[], y=[],
                    mode='markers+text',
                    marker=dict(
                        size=20,
                        color=self.colors.get(node['group'][0] if node['group'] else 'R', '#888888')
                    ),
                    text=node['label'],
                    textposition="middle center",
                    hovertext=node['title'],
                    hoverinfo='text',
                    showlegend=False
                ))
            
            fig.update_layout(
                title=f"Parallel Passage Network: '{theme}'",
                height=600,
                showlegend=False
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            return f"Error creating network: {e}"
    
    def create_comprehensive_dashboard(self) -> str:
        """Create comprehensive dashboard with multiple visualizations"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Documentary Hypothesis Research Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { margin: 20px 0; }
                h1 { color: #333; text-align: center; }
                h2 { color: #666; border-bottom: 2px solid #ddd; }
                .info-box { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Documentary Hypothesis Research Dashboard</h1>
            
            <div class="info-box">
                <h3>Source Color Coding</h3>
                <p><span style="color: #000088; font-weight: bold;">J (Jahwist)</span> - Navy Blue | 
                   <span style="color: #008888; font-weight: bold;">E (Elohist)</span> - Teal | 
                   <span style="color: #888800; font-weight: bold;">P (Priestly)</span> - Olive Yellow | 
                   <span style="color: #000000; font-weight: bold;">D (Deuteronomist)</span> - Black | 
                   <span style="color: #880000; font-weight: bold;">R (Redactor)</span> - Maroon Red</p>
            </div>
            
            <div class="chart-container">
                <h2>Source Distribution Across Biblical Books</h2>
                {source_distribution_chart}
            </div>
            
            <div class="chart-container">
                <h2>Overall Source Distribution</h2>
                {source_percentage_chart}
            </div>
            
            <div class="chart-container">
                <h2>Creation Theme Analysis</h2>
                {creation_theme_chart}
            </div>
            
            <div class="chart-container">
                <h2>Covenant Theme Analysis</h2>
                {covenant_theme_chart}
            </div>
        </body>
        </html>
        """
        
        # Generate charts
        source_dist_chart = self.create_source_distribution_chart()
        source_pct_chart = self.create_source_percentage_chart()
        creation_chart = self.create_theological_theme_analysis("creation")
        covenant_chart = self.create_theological_theme_analysis("covenant")
        
        # Replace placeholders
        html_content = html_content.format(
            source_distribution_chart=source_dist_chart,
            source_percentage_chart=source_pct_chart,
            creation_theme_chart=creation_chart,
            covenant_theme_chart=covenant_chart
        )
        
        return html_content
    
    def save_visualization(self, html_content: str, filename: str):
        """Save visualization to HTML file"""
        output_dir = Path("frontend")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Visualization saved: {file_path}")
        return str(file_path)

def main():
    """Create visualizations for Documentary Hypothesis research"""
    print("📊 Creating Documentary Hypothesis Visualizations")
    print("=" * 50)
    
    visualizer = DocumentaryHypothesisVisualizer()
    
    if not visualizer.setup_weaviate_connection():
        return
    
    # Create individual visualizations
    print("📈 Creating source distribution chart...")
    dist_chart = visualizer.create_source_distribution_chart()
    visualizer.save_visualization(dist_chart, "source_distribution.html")
    
    print("🥧 Creating source percentage chart...")
    pct_chart = visualizer.create_source_percentage_chart()
    visualizer.save_visualization(pct_chart, "source_percentages.html")
    
    print("🔍 Creating creation theme analysis...")
    creation_chart = visualizer.create_theological_theme_analysis("creation")
    visualizer.save_visualization(creation_chart, "creation_theme_analysis.html")
    
    print("📋 Creating covenant theme analysis...")
    covenant_chart = visualizer.create_theological_theme_analysis("covenant")
    visualizer.save_visualization(covenant_chart, "covenant_theme_analysis.html")
    
    print("🌐 Creating comprehensive dashboard...")
    dashboard = visualizer.create_comprehensive_dashboard()
    visualizer.save_visualization(dashboard, "documentary_hypothesis_dashboard.html")
    
    print("\n🎉 All visualizations created successfully!")
    print("📁 Files saved in frontend/ directory:")
    print("  • source_distribution.html")
    print("  • source_percentages.html") 
    print("  • creation_theme_analysis.html")
    print("  • covenant_theme_analysis.html")
    print("  • documentary_hypothesis_dashboard.html")
    print("\n🌐 Open any HTML file in your browser to view the visualizations")

if __name__ == "__main__":
    main()
