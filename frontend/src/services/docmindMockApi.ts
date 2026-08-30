import type { DocumentItem, ChatMessage, Citation } from '../types/docmind';

// Pre-populated initial mock document for instant workstation demonstration
const DEFAULT_ATTENTION_PAPER: DocumentItem = {
  id: 'doc-attention-2017',
  workspace_id: 'default',
  filename: 'Vaswani_Attention_2017.pdf',
  file_size: 2411724, // 2.4 MB
  page_count: 15,
  status: 'ready',
  file_url: '/Vaswani_Attention_2017.pdf',
  created_at: new Date(Date.now() - 3600000 * 24 * 2).toISOString(),
  pages: [
    {
      page_number: 1,
      title: 'Attention Is All You Need',
      content: `Attention Is All You Need
Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin

Abstract
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.`,
      excerpt: 'We propose the Transformer, a model architecture eschewing recurrence and relying entirely on attention mechanisms to draw global dependencies between input and output.',
      sections: [
        {
          heading: '1. Introduction',
          body: 'Recurrent neural networks, particularly long short-term memory (LSTM) and gated recurrent neural networks, have been firmly established as state of the art approaches in sequence modeling and transduction problems such as language modeling and machine translation. Multi-head self-attention allows the model to jointly attend to information from different representation subspaces at different positions.',
        },
      ],
    },
    {
      page_number: 2,
      title: 'Model Architecture',
      content: `2. Model Architecture
Most competitive neural sequence transduction models have an encoder-decoder structure. Here, the encoder maps an input sequence of symbol representations (x1, ..., xn) to a sequence of continuous representations z = (z1, ..., zn). Given z, the decoder then generates an output sequence (y1, ..., ym) of symbols one element at a time.

2.1 Encoder and Decoder Stacks
Encoder: The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers. The first is a multi-head self-attention mechanism, and the second is a simple, position-wise fully connected feed-forward network. We employ a residual connection around each of the two sub-layers, followed by layer normalization.`,
      excerpt: 'The encoder is composed of a stack of N = 6 identical layers, each containing a multi-head self-attention mechanism and a position-wise feed-forward network.',
      sections: [
        {
          heading: '2.1 Encoder Stack Details',
          body: 'That is, the output of each sub-layer is LayerNorm(x + SubLayer(x)), where SubLayer(x) is the function implemented by the sub-layer itself. To facilitate these residual connections, all sub-layers in the model, as well as the embedding layers, produce outputs of dimension d_model = 512.',
        },
      ],
    },
    {
      page_number: 3,
      title: 'Attention Mechanisms & Scaled Dot-Product',
      content: `3. Attention Mechanisms
An attention function can be described as mapping a query and a set of key-value pairs to an output, where the query, keys, values, and output are all vectors. The output is computed as a weighted sum of the values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key.

3.1 Scaled Dot-Product Attention
We call our particular attention "Scaled Dot-Product Attention". The input consists of queries and keys of dimension dk, and values of dimension dv. We compute the dot products of the query with all keys, divide each by sqrt(dk), and apply a softmax function to obtain the weights on the values.`,
      excerpt: 'Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V',
      sections: [
        {
          heading: '3.1 Scaled Dot-Product Formula',
          body: 'We compute the attention matrix simultaneously on a set of queries, packed together into a matrix Q. The keys and values are also packed together into matrices K and V.',
        },
        {
          heading: '3.2 Multi-Head Attention',
          body: 'Instead of performing a single attention function with d_model-dimensional keys, values and queries, we found it beneficial to linearly project the queries, keys and values h times with different, learned linear projections to dk, dk and dv dimensions, respectively.',
        },
      ],
    },
    {
      page_number: 14,
      title: 'Hyperparameters and Training Efficiency',
      content: `5. Training & Hyperparameters
We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million sentence pairs. Sentences were encoded using byte-pair encoding, which has a shared source-target vocabulary of about 37000 tokens.

5.1 Hardware and Schedule
We trained our models on one machine with 8 NVIDIA P100 GPUs. For the base models using the hyperparameters described throughout the paper, each training step took about 0.4 seconds. We trained the base models for a total of 100,000 steps or 12 hours. For our big models, step time was 1.0 seconds. The big models were trained for 300,000 steps (18 hours).`,
      excerpt: 'Base models were trained on 8 NVIDIA P100 GPUs for 100,000 steps (12 hours) with 0.4s per step, while big models took 300,000 steps (18 hours) with 1.0s per step.',
      sections: [
        {
          heading: '5.2 Optimizer Settings',
          body: 'We used the Adam optimizer with beta1 = 0.9, beta2 = 0.98 and epsilon = 10^-9. We varied the learning rate over the course of training according to the formula: lrate = d_model^-0.5 * min(step_num^-0.5, step_num * warmup_steps^-1.5), where warmup_steps = 4000.',
        },
      ],
    },
  ],
};

// Store mock documents in memory per workspace ID
const mockWorkspaceDocs: Record<string, DocumentItem[]> = {};

// Helper: Load documents from localStorage for persistence across sign in / sign out
function loadDocsFromStorage(workspaceId: string): DocumentItem[] {
  try {
    const raw = localStorage.getItem(`docmind_docs_${workspaceId}`);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (e) {
    console.error('Failed to parse localStorage documents:', e);
  }
  return workspaceId === 'demo' ? [{ ...DEFAULT_ATTENTION_PAPER, workspace_id: workspaceId }] : [];
}

// Helper: Save documents to localStorage
function saveDocsToStorage(workspaceId: string, docs: DocumentItem[]) {
  try {
    localStorage.setItem(`docmind_docs_${workspaceId}`, JSON.stringify(docs));
  } catch (e) {
    console.error('Failed to save documents to localStorage:', e);
  }
}

// Helper: Extract real page count from PDF File ArrayBuffer
async function extractRealPdfMetadata(file: File): Promise<{ pageCount: number }> {
  try {
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    const textDecoder = new TextDecoder('latin1');
    const pdfText = textDecoder.decode(bytes);

    // 1. Search for /Type /Pages /Count N or /Count N in PDF Catalog
    const countMatch = pdfText.match(/\/Type\s*\/Pages[^]*?\/Count\s+(\d+)/i) || pdfText.match(/\/Count\s+(\d+)\b/i);
    let detectedPages = 0;
    if (countMatch && countMatch[1]) {
      detectedPages = parseInt(countMatch[1], 10);
    }

    // 2. Fallback: Count /Type /Page objects (excluding /Pages)
    if (!detectedPages || detectedPages <= 0 || detectedPages > 3000) {
      const pageMatches = pdfText.match(/\/Type\s*\/Page\b(?!\s*s)/gi);
      if (pageMatches && pageMatches.length > 0) {
        detectedPages = pageMatches.length;
      }
    }

    const finalPages = (detectedPages > 0 && detectedPages <= 3000) ? detectedPages : 10;
    return { pageCount: finalPages };
  } catch (e) {
    console.error('Error reading PDF page count:', e);
    return { pageCount: 10 };
  }
}

export const docmindMockApi = {
  // 1. Fetch workspace documents (persisted in localStorage across sessions)
  getWorkspaceDocuments: async (workspaceId: string): Promise<DocumentItem[]> => {
    await new Promise((res) => setTimeout(res, 150)); // Latency
    if (!mockWorkspaceDocs[workspaceId]) {
      mockWorkspaceDocs[workspaceId] = loadDocsFromStorage(workspaceId);
    }
    return mockWorkspaceDocs[workspaceId];
  },

  // 2. Mock PDF Upload function with progress callback & localStorage persistence
  uploadDocument: async (
    workspaceId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DocumentItem> => {
    // Validate File Format
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      throw new Error('Invalid file format. DocMind supports PDF documents only (.pdf).');
    }

    // Validate File Size (25 MB max)
    const MAX_SIZE_BYTES = 25 * 1024 * 1024;
    if (file.size > MAX_SIZE_BYTES) {
      throw new Error(
        `File size exceeds 25 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB). Please select a smaller PDF.`
      );
    }

    // Simulate progress 0% -> 100%
    for (let p = 10; p <= 90; p += 20) {
      if (onProgress) onProgress(p);
      await new Promise((res) => setTimeout(res, 100));
    }
    if (onProgress) onProgress(100);

    const docId = `doc-${Date.now()}`;
    const { pageCount } = await extractRealPdfMetadata(file);
    const fileUrl = URL.createObjectURL(file);

    const newDoc: DocumentItem = {
      id: docId,
      workspace_id: workspaceId,
      filename: file.name,
      file_size: file.size,
      page_count: pageCount,
      status: 'ready',
      file_url: fileUrl,
      created_at: new Date().toISOString(),
      pages: Array.from({ length: pageCount }, (_, i) => ({
        page_number: i + 1,
        title: `${file.name.replace(/\.pdf$/i, '')} — Page ${i + 1}`,
        content: `Document: ${file.name}\nPage ${i + 1} of ${pageCount}\n\nIngested text block extracted from page ${i + 1} of "${file.name}".\n\nThis page contains continuous sequence representations, formulas, and structural passages processed by DocMind AI vector search indexing for workspace RAG queries.`,
        excerpt: `Passage excerpt from page ${i + 1} of ${file.name}.`,
        sections: [
          {
            heading: `Section ${i + 1}.1 — ${file.name.replace(/\.pdf$/i, '')} Overview`,
            body: `Detailed text passage extracted from page ${i + 1} of ${file.name}. Vector embeddings indexed for grounded question answering.`,
          },
        ],
      })),
    };

    if (!mockWorkspaceDocs[workspaceId]) {
      mockWorkspaceDocs[workspaceId] = loadDocsFromStorage(workspaceId);
    }

    // Deduplicate by ID before unshifting
    const existing = mockWorkspaceDocs[workspaceId].filter((d) => d.id !== docId && d.filename !== file.name);
    mockWorkspaceDocs[workspaceId] = [newDoc, ...existing];

    // Persist to localStorage so file stays permanently across login/logout
    saveDocsToStorage(workspaceId, mockWorkspaceDocs[workspaceId]);

    return newDoc;
  },

  // 3. Delete Document function
  deleteDocument: async (workspaceId: string, documentId: string): Promise<void> => {
    await new Promise((res) => setTimeout(res, 150));
    if (!mockWorkspaceDocs[workspaceId]) {
      mockWorkspaceDocs[workspaceId] = loadDocsFromStorage(workspaceId);
    }
    mockWorkspaceDocs[workspaceId] = mockWorkspaceDocs[workspaceId].filter((d) => d.id !== documentId);
    saveDocsToStorage(workspaceId, mockWorkspaceDocs[workspaceId]);
  },

  // 4. Mock grounded chat response generator with citations
  sendChatMessage: async (
    _workspaceId: string,
    document: DocumentItem,
    userQuery: string
  ): Promise<ChatMessage> => {
    await new Promise((res) => setTimeout(res, 600)); // Latency

    const lowerQuery = userQuery.toLowerCase();

    // Default citation references
    let responseText = '';
    let citations: Citation[] = [];

    if (lowerQuery.includes('training') || lowerQuery.includes('gpu') || lowerQuery.includes('hardware') || lowerQuery.includes('time') || lowerQuery.includes('cost')) {
      responseText = `According to the training specifications, the base Transformer models were trained on 8 NVIDIA P100 GPUs for 100,000 steps [Page 14], taking approximately 12 hours total with 0.4 seconds per step. The bigger model variations were trained for 300,000 steps over 18 hours [Page 14].`;
      citations = [
        {
          id: 'cite-14-1',
          page_number: 14,
          document_id: document.id,
          document_name: document.filename,
          section_title: '5.1 Hardware and Schedule',
          snippet: 'We trained our models on one machine with 8 NVIDIA P100 GPUs. For the base models... each training step took about 0.4 seconds (100,000 steps or 12 hours).',
          relevance_score: 0.958,
          bounding_box: { x: 10, y: 35, width: 80, height: 25 },
        },
      ];
    } else if (lowerQuery.includes('formula') || lowerQuery.includes('attention') || lowerQuery.includes('scaled') || lowerQuery.includes('dot') || lowerQuery.includes('math')) {
      responseText = `The Scaled Dot-Product Attention mechanism computes attention weights by taking the dot product of queries with keys, scaling by 1/sqrt(d_k), and applying softmax [Page 3]. Multi-head attention projects queries, keys, and values h times into lower-dimensional subspaces [Page 3].`;
      citations = [
        {
          id: 'cite-3-1',
          page_number: 3,
          document_id: document.id,
          document_name: document.filename,
          section_title: '3.1 Scaled Dot-Product Attention',
          snippet: 'Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V. We compute the dot products of query with keys, divide by sqrt(d_k), and apply softmax.',
          relevance_score: 0.974,
          bounding_box: { x: 12, y: 40, width: 76, height: 28 },
        },
      ];
    } else if (lowerQuery.includes('architecture') || lowerQuery.includes('encoder') || lowerQuery.includes('decoder') || lowerQuery.includes('layer')) {
      responseText = `The Transformer architecture features an encoder-decoder structure where the encoder consists of N = 6 identical stacked layers [Page 2]. Each layer contains a multi-head self-attention sub-layer and a position-wise feed-forward network with residual layer normalization [Page 2] [Page 1].`;
      citations = [
        {
          id: 'cite-2-1',
          page_number: 2,
          document_id: document.id,
          document_name: document.filename,
          section_title: '2.1 Encoder and Decoder Stacks',
          snippet: 'The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers: multi-head self-attention and position-wise feed-forward network.',
          relevance_score: 0.941,
          bounding_box: { x: 15, y: 20, width: 70, height: 30 },
        },
        {
          id: 'cite-1-1',
          page_number: 1,
          document_id: document.id,
          document_name: document.filename,
          section_title: 'Abstract',
          snippet: 'We propose the Transformer, a model architecture eschewing recurrence and relying entirely on attention mechanisms to draw global dependencies.',
          relevance_score: 0.912,
          bounding_box: { x: 10, y: 50, width: 80, height: 20 },
        },
      ];
    } else {
      responseText = `Based on the ingested document "${document.filename}", the text discusses attention mechanisms, model architecture, and training setups [Page 1]. Multi-head self-attention enables parallel computation without recurrence [Page 3].`;
      citations = [
        {
          id: 'cite-1-def',
          page_number: 1,
          document_id: document.id,
          document_name: document.filename,
          section_title: '1. Introduction',
          snippet: 'Multi-head self-attention allows the model to jointly attend to information from different representation subspaces at different positions.',
          relevance_score: 0.885,
          bounding_box: { x: 10, y: 60, width: 80, height: 25 },
        },
      ];
    }

    return {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      content: responseText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations,
    };
  },
};
