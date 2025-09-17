using Microsoft.AspNetCore.Http.HttpResults;
using Simuvirtu.Interfaces;
using System.Text.Json;
using System.Threading.Tasks;

namespace Simuvirtu.Services
{
    public class CryptoService : ICryptoService
    {
        private readonly HttpClient _httpClient;

        public CryptoService(HttpClient httpClient) 
        { 
            _httpClient = httpClient;
        }
        public async Task<decimal> GetCryptoPrice(string symbol)
        {
            var res = await _httpClient.GetAsync($"https://api.binance.com/api/v3/ticker/price?symbol={symbol.ToUpper().Trim()}USDT");
            res.EnsureSuccessStatusCode();

            var content = await res.Content.ReadAsStringAsync();
            
            using var doc = JsonDocument.Parse(content);
            var priceStr = doc.RootElement.GetProperty("price").GetString();

            return decimal.Parse(priceStr);
        }
    }
}
