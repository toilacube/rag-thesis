import React, { FC, useMemo, useEffect, useState, ClassAttributes, AnchorHTMLAttributes } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/popover";
import { Skeleton } from "@/components/skeleton";
import { Divider } from "@/components/divider";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { api } from "@/lib/api"; // Keep for potential future direct fetches if needed, or for consistency
import { FileIcon, defaultStyles } from "react-file-icon"; // Keep if citations have file info

// Re-introducing Citation-related interfaces
export interface CitationMetadata {
  kb_id?: string | number; // Knowledge Base ID
  document_id?: string | number; // Document ID
  [key: string]: any; // Allow other metadata fields
}

export interface Citation {
  id: number; // Or string, depending on how backend sends it. Usually an index.
  text: string;
  metadata: CitationMetadata;
  // Optional fields based on your previous structure
  file_name?: string;
  knowledge_base_name?: string;
}


// For Popover display
interface CitationInfo {
  knowledge_base_name: string;
  document_file_name: string;
}

// Main Answer Component
export const Answer: FC<{
  markdown: string;
  citations?: Citation[]; // Citations are now optional
}> = ({ markdown, citations = [] }) => { // Default to empty array if undefined
  const [citationInfoMap, setCitationInfoMap] = useState<Record<string, CitationInfo>>({});

  // Logic for fetching KB/Document names for citations if kb_id and document_id are present
  // This logic might need adjustment if the backend sends file_name and kb_name directly in Citation object
  useEffect(() => {
    const fetchCitationDetails = async () => {
      const infoMap: Record<string, CitationInfo> = {};
      if (!citations || citations.length === 0) {
        setCitationInfoMap({});
        return;
      }

      for (const citation of citations) {
        const { kb_id, document_id } = citation.metadata;
        if (!kb_id || !document_id) continue;

        const key = `${kb_id}-${document_id}`;
        if (infoMap[key]) continue; // Already fetched or fetching

        // If backend now sends names directly, this fetch might be redundant
        if (citation.knowledge_base_name && citation.file_name) {
            infoMap[key] = {
                knowledge_base_name: citation.knowledge_base_name,
                document_file_name: citation.file_name,
            };
            continue;
        }

        // Fallback to fetching if names are not directly provided
        try {
          // This assumes your API structure for fetching KB/Doc names.
          // Adjust if these endpoints are different or if data comes differently.
          const kbPromise = citation.knowledge_base_name ? Promise.resolve({ name: citation.knowledge_base_name }) : api.get(`/api/knowledge-base/${kb_id}`);
          const docPromise = citation.file_name ? Promise.resolve({ file_name: citation.file_name }) : api.get(`/api/knowledge-base/${kb_id}/documents/${document_id}`);
          
          const [kbData, docData] = await Promise.all([kbPromise, docPromise]);

          infoMap[key] = {
            knowledge_base_name: kbData.name,
            document_file_name: docData.file_name,
          };
        } catch (error) {
          console.error(`Failed to fetch citation details for ${key}:`, error);
          // Store a fallback or leave it out
          infoMap[key] = {
             knowledge_base_name: `KB ${kb_id}`,
             document_file_name: `Doc ${document_id}`
          }
        }
      }
      setCitationInfoMap(infoMap);
    };

    if (citations.length > 0) {
      fetchCitationDetails();
    }
  }, [citations]);


  const CitationLink = useMemo(() => (
    props: ClassAttributes<HTMLAnchorElement> & AnchorHTMLAttributes<HTMLAnchorElement>
  ) => {
    if (!citations || citations.length === 0) {
        // If no citations, render as a normal link or placeholder
        return <a {...props}>[{props.href}]</a>;
    }

    const citationMatch = props.href?.match(/^(\d+)$/); // Expecting href to be just the citation number e.g., "1"
    const citationIndex = citationMatch ? parseInt(citationMatch[1], 10) - 1 : -1; // 1-based index from markdown
    
    const citation = (citationIndex >= 0 && citationIndex < citations.length) ? citations[citationIndex] : null;

    if (!citation) {
      // If citation not found by index, render as a simple link or placeholder
      return <a {...props}>[{props.href}]</a>;
    }
    
    const citationKey = citation.metadata.kb_id && citation.metadata.document_id 
        ? `${citation.metadata.kb_id}-${citation.metadata.document_id}` 
        : null;
    const displayInfo = citationKey ? citationInfoMap[citationKey] : null;
    const popoverFileName = displayInfo?.document_file_name || citation.file_name || "Document";
    const popoverKbName = displayInfo?.knowledge_base_name || citation.knowledge_base_name || "Knowledge Base";


    return (
      <Popover>
        <PopoverTrigger asChild>
          <a
            {...props}
            href="#" // Prevent navigation
            role="button"
            className="inline-flex items-center gap-0.5 px-1 py-0 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors relative"
            title={`Citation ${citationIndex + 1}: ${citation.text.substring(0, 50)}...`}
          >
            [{citationIndex + 1}]
          </a>
        </PopoverTrigger>
        <PopoverContent
          side="top"
          align="start"
          className="max-w-md w-[calc(100vw-80px)] p-3 rounded-lg shadow-lg z-50" // Ensure z-index
        >
          <div className="text-xs space-y-2">
            {(displayInfo || citation.file_name) && (
              <div className="flex items-center gap-1.5 text-xs font-medium text-gray-700 bg-gray-50 p-1.5 rounded">
                <div className="w-4 h-4 flex-shrink-0 flex items-center justify-center">
                   <div style={{ width: '16px', height: '16px' }}>
                     <FileIcon
                       extension={(popoverFileName.split(".").pop() || "").toLowerCase()}
                       {...(defaultStyles[(popoverFileName.split(".").pop() || "").toLowerCase() as keyof typeof defaultStyles] || {})}
                     />
                   </div>
                </div>
                <span className="truncate" title={`${popoverKbName} / ${popoverFileName}`}>
                  {popoverKbName} / {popoverFileName}
                </span>
              </div>
            )}
            {displayInfo && <Divider className="my-1"/>}
            <p className="text-gray-700 leading-relaxed max-h-32 overflow-y-auto">
                {citation.text}
            </p>
            {Object.keys(citation.metadata).length > 0 && (
              <>
                <Divider className="my-1"/>
                <div className="text-xxs text-gray-500 bg-gray-50 p-1.5 rounded"> {/* even smaller text for debug */}
                  <div className="font-medium mb-1">Debug Info:</div>
                  <pre className="whitespace-pre-wrap text-xxs">{JSON.stringify(citation.metadata, null, 2)}</pre>
                </div>
              </>
            )}
          </div>
        </PopoverContent>
      </Popover>
    );
  }, [citations, citationInfoMap]);

  // Markdown parsing for citations: [Citation:1] or [[Citation:1]] -> [citation](1)
  // Or a simpler [1] if the backend guarantees that. Assuming backend sends [1], [2] etc.
  // The `useChat` `Message` type from `ai/react` doesn't have a standard `citations` field.
  // This component assumes `citations` are passed in separately.
  const preprocessedMarkdown = useMemo(() => {
    if (!markdown) return "";
    // This regex looks for [number] and converts it to a link that CitationLink can pick up.
    // E.g., "Response with source [1]." -> "Response with source [citation](1)."
    // This step is crucial if backend sends citations like [1], [2]
    // If backend sends markdown like [citation](1) directly, this step might not be needed.
    return markdown.replace(/\[(\d+)\]/g, (_match, p1) => `[citation](${p1})`);
  }, [markdown]);


  if (markdown === undefined || markdown === null) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="max-w-sm h-4 bg-zinc-200" />
        <Skeleton className="max-w-lg h-4 bg-zinc-200" />
        {/* ... more skeletons */}
      </div>
    );
  }

  return (
    <div className="prose prose-sm max-w-full">
      <Markdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Only override 'a' if citations are present and feature is enabled
          a: (citations && citations.length > 0) ? CitationLink : undefined,
        }}
      >
        {preprocessedMarkdown}
      </Markdown>
    </div>
  );
};