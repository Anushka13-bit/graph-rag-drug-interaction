// API Client for DDI Analyzer FastAPI Backend

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface GraphNode {
  id: string;
  label: string;
  type?: string;
  x?: number;
  y?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  severity: 'major' | 'moderate' | 'minor';
}

export interface InteractionGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface InteractionDetail {
  drug_a: string;
  drug_b: string;
  interaction_type: string;
  severity: 'mild' | 'moderate' | 'severe';
  description: string;
  evidence_count: number;
  sources: string[];
}

export interface DrugInteractionResponse {
  drugs_queried: string[];
  interactions: InteractionDetail[];
  graph_data: InteractionGraphData;
  summary: string;
  total_interactions: number;
}

/**
 * Fetch interaction graph data between two drugs.
 * Attempts real API call first, then falls back to fallback structure if unreachable.
 */
export async function getDrugInteractions(drug1: string, drug2: string): Promise<InteractionGraphData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/graph/interactions/${encodeURIComponent(drug1)}/${encodeURIComponent(drug2)}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    
    // Map backend graph payload to graph nodes & edges if data returned
    if (Array.isArray(data) && data.length > 0) {
      const nodesMap = new Map<string, GraphNode>();
      const edges: GraphEdge[] = [];
      
      data.forEach((path: any) => {
        if (path.drug1) nodesMap.set(path.drug1.toUpperCase(), { id: path.drug1.toUpperCase(), label: path.drug1.toUpperCase() });
        if (path.drug2) nodesMap.set(path.drug2.toUpperCase(), { id: path.drug2.toUpperCase(), label: path.drug2.toUpperCase() });
        
        if (path.drug1 && path.drug2) {
          edges.push({
            source: path.drug1.toUpperCase(),
            target: path.drug2.toUpperCase(),
            severity: (path.severity?.toLowerCase() || 'major') as 'major' | 'moderate' | 'minor',
          });
        }
      });

      return {
        nodes: Array.from(nodesMap.values()),
        edges,
      };
    }
  } catch (error) {
    console.warn('// MOCK: Backend endpoint unreachable or returned empty graph data for interactions, using client state.', error);
  }
  return null;
}

/**
 * Fetch entity graph neighborhood for a single drug.
 */
export async function getEntityNeighborhood(drugName: string): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/graph/entity/${encodeURIComponent(drugName)}`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return await response.json();
  } catch (error) {
    console.warn(`// MOCK: Could not fetch graph neighborhood for ${drugName}.`, error);
    return null;
  }
}

/**
 * Call Graph-RAG Query endpoint.
 */
export async function queryDDIReasoning(question: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: 5, include_graph_paths: true, stream: false }),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return await response.json();
  } catch (error) {
    console.warn('// MOCK: Query reasoning endpoint offline.', error);
    return null;
  }
}

/**
 * Call the structured /query/interact endpoint to get DrugInteractionResponse.
 */
export async function analyzeInteractions(question: string): Promise<DrugInteractionResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/query/interact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: 5, include_graph_paths: true, stream: false }),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to analyze interactions:', error);
    return null;
  }
}
