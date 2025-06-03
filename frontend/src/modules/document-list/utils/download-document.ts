"use server";

import { api } from "@/lib/api-server"; // Your updated api setup
import { ApiError } from "@/lib/api";   // Your ApiError class

export const downloadDocumentAction = async (documentId: number) => {
  if (!documentId) {
    return { success: false, message: "Document ID is missing." };
  }

  try {
    // api.get will now:
    // - Return parsed JSON if Content-Type is application/json
    // - Return a Response object for other successful Content-Types (like files)
    // - Throw an ApiError for HTTP errors (4xx, 5xx) or network issues
    const resultFromApi = await api.get(`/api/document/${documentId}/download`);

    // Ensure we received a Response object, as expected for a file download
    if (!(resultFromApi instanceof Response)) {
      // This would happen if the server incorrectly sent Content-Type: application/json for a file,
      // or if fetchApi's logic changes unexpectedly.
      console.error(
        `Download error for document ${documentId}: Expected a Response object from API, but got:`,
        typeof resultFromApi,
        resultFromApi
      );
      return { success: false, message: "API returned an unexpected data format for the document." };
    }

    const response: Response = resultFromApi; // Now we know it's a Response object

    // The `fetchApi` already checks for `!response.ok` and throws an ApiError.
    // So, if we reach here, `response.ok` should be true.
    // You could add an assertion here if you're paranoid:
    // if (!response.ok) {
    //   console.error(`Unexpected !response.ok for document ${documentId} after fetchApi. Status: ${response.status}`);
    //   return { success: false, message: `Download failed with status: ${response.status}`};
    // }

    console.log(`Processing download for document ${documentId}. Response status: ${response.status}, ok: ${response.ok}`);

    const blob = await response.blob();
    console.log(`Document ${documentId}: Blob received. Type: ${blob.type}, Size: ${blob.size}`);

    if (blob.size === 0) {
      console.warn(`Document ${documentId}: Downloaded blob is empty.`);
      // You might want to treat this as an error or handle it specifically
      // return { success: false, message: "Downloaded document is empty." };
    }

    const arrayBuffer = await blob.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer); // Buffer is available in Node.js runtime (Server Actions)

    return {
      success: true,
      data: buffer.toString("base64"),
      contentType: blob.type || 'application/octet-stream', // Use blob.type, fallback if it's missing
    };

  } catch (error) {
    console.error(`Error in downloadDocumentAction for documentId ${documentId}:`, error);
    let errorMessage = "An unexpected error occurred while downloading the document.";

    if (error instanceof ApiError) {
      // ApiError already contains a status and a message from fetchApi
      errorMessage = `Failed to download document: ${error.message}${error.status ? ` (Status: ${error.status})` : ''}`;
    } else if (error instanceof Error) {
      errorMessage = error.message; // For other JS errors
    }
    // For non-Error objects thrown (less common)
    else if (typeof error === 'string') {
        errorMessage = error;
    }

    return { success: false, message: errorMessage };
  }
};