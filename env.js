export default function handler(request, response) {
  response.status(200).json({
    // [Final Fix] Use the prefixed variable name
    API_BASE_URL: process.env.VITE_API_BASE_URL,
  });
}