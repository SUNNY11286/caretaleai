"""
Citation Generator Component
Implements transparent source attribution for all medical information.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from ..models.knowledge_document import KnowledgeDocument


@dataclass
class Citation:
    """A citation with formatted text and metadata"""
    citation_text: str
    document_id: str
    source_name: str
    url: Optional[str]
    snippet: str


@dataclass
class GroundedResponse:
    """A response with grounded citations"""
    response_text: str
    citations: List[Citation]
    source_documents: List[KnowledgeDocument]


class CitationGenerator:
    """
    Generates transparent citations for medical information.
    Ensures all responses are traceable to authoritative sources.
    """

    def __init__(self):
        """Initialize the citation generator."""
        pass

    def generate_citations(
        self,
        response_text: str,
        source_documents: List[KnowledgeDocument],
        citation_style: str = "APA"
    ) -> List[Citation]:
        """
        Generate citations for a response based on source documents.
        
        Args:
            response_text: The generated response text
            source_documents: Documents used to generate the response
            citation_style: Citation style (APA, MLA, Chicago, Vancouver)
            
        Returns:
            List of formatted citations
        """
        citations = []
        
        for doc in source_documents:
            citation = self._create_citation(doc, response_text, citation_style)
            citations.append(citation)
        
        return citations

    def create_grounded_response(
        self,
        response_text: str,
        source_documents: List[KnowledgeDocument],
        include_inline_citations: bool = True
    ) -> GroundedResponse:
        """
        Create a grounded response with embedded citations.
        
        Args:
            response_text: The generated response text
            source_documents: Documents used to generate the response
            include_inline_citations: Whether to include inline citation markers
            
        Returns:
            GroundedResponse with citations
        """
        citations = self.generate_citations(response_text, source_documents)
        
        # Add inline citation markers if requested
        if include_inline_citations:
            response_text = self._add_inline_citations(response_text, citations)
        
        return GroundedResponse(
            response_text=response_text,
            citations=citations,
            source_documents=source_documents
        )

    def _create_citation(
        self,
        document: KnowledgeDocument,
        response_text: str,
        citation_style: str
    ) -> Citation:
        """
        Create a citation for a single document.
        
        Args:
            document: Source document
            response_text: Response text to extract snippet from
            citation_style: Citation style
            
        Returns:
            Formatted citation
        """
        # Format citation based on style
        if citation_style == "APA":
            citation_text = self._format_apa(document)
        elif citation_style == "Vancouver":
            citation_text = self._format_vancouver(document)
        else:
            # Default to simple format
            citation_text = self._format_simple(document)
        
        # Extract relevant snippet from document
        snippet = self._extract_snippet(document.content, response_text)
        
        return Citation(
            citation_text=citation_text,
            document_id=document.document_id,
            source_name=document.source.organization_name,
            url=document.citation_format.url or document.source.url,
            snippet=snippet
        )

    def _format_apa(self, document: KnowledgeDocument) -> str:
        """
        Format citation in APA style.
        
        Args:
            document: Source document
            
        Returns:
            APA-formatted citation
        """
        metadata = document.metadata
        source = document.source
        
        # Basic APA format: Organization. (Year). Title. URL
        year = metadata.publication_date.year
        title = metadata.title
        org = source.organization_name
        url = document.citation_format.url or source.url or ""
        
        citation = f"{org}. ({year}). {title}."
        if url:
            citation += f" Retrieved from {url}"
        
        return citation

    def _format_vancouver(self, document: KnowledgeDocument) -> str:
        """
        Format citation in Vancouver style.
        
        Args:
            document: Source document
            
        Returns:
            Vancouver-formatted citation
        """
        metadata = document.metadata
        source = document.source
        
        # Vancouver format: Organization. Title. Year.
        org = source.organization_name
        title = metadata.title
        year = metadata.publication_date.year
        
        return f"{org}. {title}. {year}."

    def _format_simple(self, document: KnowledgeDocument) -> str:
        """
        Format citation in simple readable format.
        
        Args:
            document: Source document
            
        Returns:
            Simple formatted citation
        """
        metadata = document.metadata
        source = document.source
        
        return f"{metadata.title} - {source.organization_name}"

    def _extract_snippet(
        self,
        document_content: str,
        response_text: str,
        max_length: int = 200
    ) -> str:
        """
        Extract a relevant snippet from the document.
        
        Args:
            document_content: Full document content
            response_text: Response text to match against
            max_length: Maximum snippet length
            
        Returns:
            Relevant snippet from document
        """
        # Simple implementation: take first max_length characters
        # In production, use more sophisticated matching
        snippet = document_content[:max_length]
        if len(document_content) > max_length:
            snippet += "..."
        
        return snippet

    def _add_inline_citations(
        self,
        response_text: str,
        citations: List[Citation]
    ) -> str:
        """
        Add inline citation markers to response text.
        
        Args:
            response_text: Original response text
            citations: List of citations
            
        Returns:
            Response text with inline citation markers
        """
        # Add citation list at the end
        if not citations:
            return response_text
        
        citation_section = "\n\nSources:\n"
        for i, citation in enumerate(citations, start=1):
            citation_section += f"[{i}] {citation.citation_text}\n"
        
        return response_text + citation_section

    def validate_citations(
        self,
        grounded_response: GroundedResponse
    ) -> Dict[str, bool]:
        """
        Validate that all citations are properly formatted and traceable.
        
        Args:
            grounded_response: Response with citations to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "has_citations": len(grounded_response.citations) > 0,
            "all_documents_cited": len(grounded_response.citations) == len(grounded_response.source_documents),
            "all_citations_have_sources": all(
                citation.source_name and citation.citation_text
                for citation in grounded_response.citations
            ),
            "all_citations_traceable": all(
                citation.document_id in [doc.document_id for doc in grounded_response.source_documents]
                for citation in grounded_response.citations
            )
        }
        
        results["valid"] = all(results.values())
        
        return results
