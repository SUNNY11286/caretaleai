/**
 * Knowledge Base Demo
 * Demonstrates loading and using the CARETALE AI knowledge base
 */

import { createAndLoadKnowledgeBase } from '../src/knowledge-context-layer/knowledge-base-loader';
import { KnowledgeBaseCategory } from '../src/knowledge-context-layer/types';
import { MedicalDomain } from '../src/shared/types/knowledge-document';

function main() {
  console.log('=== CARETALE AI Knowledge Base Demo ===\n');

  // Load the knowledge base
  console.log('Loading knowledge base...');
  const knowledgeBase = createAndLoadKnowledgeBase();
  console.log('');

  // Display statistics
  console.log('Knowledge Base Statistics:');
  const stats = knowledgeBase.getStatistics();
  console.log(`  Total documents: ${stats.total_documents}`);
  console.log(`  Validated: ${stats.validated}`);
  console.log(`  Pending review: ${stats.pending_review}`);
  console.log(`  Outdated: ${stats.outdated}`);
  console.log('');

  console.log('Documents by Category:');
  console.log(`  Clinical Guidelines: ${stats.category_clinical_guidelines}`);
  console.log(`  Educational Content: ${stats.category_educational_content}`);
  console.log(`  Drug Information: ${stats.category_drug_information}`);
  console.log(`  Care Protocols: ${stats.category_care_protocols}`);
  console.log('');

  // Get clinical guidelines
  console.log('=== Clinical Guidelines ===');
  const guidelines = knowledgeBase.getDocumentsByCategory(KnowledgeBaseCategory.CLINICAL_GUIDELINES);
  guidelines.forEach((doc) => {
    console.log(`\n${doc.metadata.title}`);
    console.log(`  Source: ${doc.source.name}`);
    console.log(`  Domain: ${doc.domain}`);
    console.log(`  Last Updated: ${doc.lastUpdated.toISOString().split('T')[0]}`);
    console.log(`  Citation: ${doc.citationFormat.shortForm}`);
  });
  console.log('');

  // Get drug information
  console.log('=== Drug Information ===');
  const drugs = knowledgeBase.getDocumentsByCategory(KnowledgeBaseCategory.DRUG_INFORMATION);
  drugs.forEach((doc) => {
    console.log(`\n${doc.metadata.title}`);
    console.log(`  Source: ${doc.source.name}`);
    console.log(`  Keywords: ${doc.metadata.keywords.join(', ')}`);
  });
  console.log('');

  // Get documents by domain
  console.log('=== Cardiology Documents ===');
  const cardiologyDocs = knowledgeBase.getDocumentsByDomain(MedicalDomain.CARDIOLOGY);
  console.log(`Found ${cardiologyDocs.length} cardiology documents:`);
  cardiologyDocs.forEach((doc) => {
    console.log(`  - ${doc.metadata.title} (${doc.source.authority})`);
  });
  console.log('');

  // Get a specific document
  console.log('=== Specific Document Example ===');
  const heartFailureDoc = knowledgeBase.getDocument('cg-001-heart-failure');
  if (heartFailureDoc) {
    console.log(`Title: ${heartFailureDoc.metadata.title}`);
    console.log(`Source: ${heartFailureDoc.source.name}`);
    console.log(`\nContent Preview (first 200 chars):`);
    console.log(heartFailureDoc.content.substring(0, 200) + '...');
    console.log(`\nFull Citation:`);
    console.log(heartFailureDoc.citationFormat.apa);
  }
  console.log('');

  // Check for outdated documents
  console.log('=== Document Maintenance ===');
  const outdated = knowledgeBase.getOutdatedDocuments(365);
  if (outdated.length > 0) {
    console.log(`Found ${outdated.length} documents older than 365 days:`);
    outdated.forEach((doc) => {
      const age = Math.floor(
        (Date.now() - doc.lastUpdated.getTime()) / (1000 * 60 * 60 * 24)
      );
      console.log(`  - ${doc.metadata.title} (${age} days old)`);
    });
  } else {
    console.log('All documents are up to date (less than 365 days old)');
  }
  console.log('');

  console.log('=== Demo Complete ===');
}

// Run the demo
main();
