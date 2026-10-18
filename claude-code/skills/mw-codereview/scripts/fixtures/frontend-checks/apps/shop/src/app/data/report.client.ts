export async function loadReport(): Promise<unknown> {
  const response = await fetch('https://api.example.com/reports/latest');
  return response.json();
}
