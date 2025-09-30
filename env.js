export default function handler(request, response) {
  // This function runs on Vercel's servers, not in the user's browser.
  // It securely reads the environment variable and sends it to the frontend.
  response.status(200).json({
    API_BASE_URL: process.env.API_BASE_URL,
  });
}