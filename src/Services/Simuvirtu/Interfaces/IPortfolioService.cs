using Simuvirtu.DTOs;
using Simuvirtu.Models;

namespace Simuvirtu.Interfaces
{
    public interface IPortfolioService
    {
        Task AddMoney(string userId, AddMoney money);
        Task BuyAsset(string userId, TradeAsset trade);
        Task SellAsset(string userId, TradeAsset trade);
        Task<Dictionary<string, object>> GetPortfolio(string userId);
    }
}
