# Documentary Hypothesis Research Functions for Elysia
# These functions are automatically available to Elysia

from documentary_hypothesis_elysia_tool import DocumentaryHypothesisResearchTool

# Initialize research tool
research_tool = DocumentaryHypothesisResearchTool()
research_tool.setup_weaviate_connection()
research_tool.load_wiki_source_data()

def analyze_source_distribution(*args, **kwargs):
    return research_tool.analyze_source_distribution(*args, **kwargs)

def find_parallel_passages(*args, **kwargs):
    return research_tool.find_parallel_passages(*args, **kwargs)

def compare_source_theology(*args, **kwargs):
    return research_tool.compare_source_theology(*args, **kwargs)

def generate_research_report(*args, **kwargs):
    return research_tool.generate_research_report(*args, **kwargs)

def create_visual_analysis(*args, **kwargs):
    return research_tool.create_visual_analysis(*args, **kwargs)

def search_source_characteristics(*args, **kwargs):
    return research_tool.search_source_characteristics(*args, **kwargs)

