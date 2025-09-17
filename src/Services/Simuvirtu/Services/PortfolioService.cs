using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;
using Simuvirtu.Data;
using Simuvirtu.DTOs;
using Simuvirtu.Interfaces;
using Simuvirtu.Models;
using System.Collections;

namespace Simuvirtu.Services
{
    public class PortfolioService : IPortfolioService
    {
        private readonly ApplicationDbContext _dbContext;
        private readonly ICryptoService _cryptoService;

        public PortfolioService(ApplicationDbContext dbContext, ICryptoService cryptoService) 
        {
            _dbContext = dbContext;
            _cryptoService = cryptoService;
        }
        public async Task AddMoney(string userId, AddMoney money)
        {
            var user = _dbContext.Users.Include(u => u.Portfolio).FirstOrDefault(u => u.Id == userId);
            if (user == null) throw new Exception("User not found");
            if (user.Portfolio == null) throw new Exception("Portfolio not found");
            var portfolio = user.Portfolio;
            portfolio.TotalAddedMoney += money.amount;
            portfolio.AvailableMoney += money.amount;
            await _dbContext.SaveChangesAsync();
        }

        public async Task BuyAsset(string userId, TradeAsset trade)
        {
            var user = _dbContext.Users.Include(u => u.Portfolio).ThenInclude(p => p.Assets).FirstOrDefault(u => u.Id == userId);
            if (user == null) throw new Exception("User not found");
            if (user.Portfolio == null) throw new Exception("Portfolio not found");
            var portfolio = user.Portfolio;
            decimal price = await _cryptoService.GetCryptoPrice(trade.Symbol);
            decimal totalCost = price * (decimal)trade.Quantity;

            if (totalCost > portfolio.AvailableMoney) throw new InvalidOperationException("Insufficient funds");

            var asset = await _dbContext.Assets.FirstOrDefaultAsync(a => a.PortfolioId == portfolio.Id && a.Symbol == trade.Symbol);

            if (asset != null)
            {
                asset.Quantity += trade.Quantity;
            }
            else
            {
                asset = new Asset
                {
                    PortfolioId = portfolio.Id,
                    Symbol = trade.Symbol,
                    Quantity = trade.Quantity
                };
                await _dbContext.Assets.AddAsync(asset);
            }
            var transaction = new Transaction 
            { 
                PortfolioId = portfolio.Id,
                Symbol = trade.Symbol,
                Quantity = trade.Quantity,
                Price = price,
                TimeStamp = DateTime.UtcNow,
            };
            await _dbContext.Transactions.AddAsync(transaction);
            
            portfolio.AvailableMoney -= totalCost;
            await _dbContext.SaveChangesAsync();
        }

        public async Task SellAsset(string userId, TradeAsset trade)
        {
            var user = _dbContext.Users.Include(u => u.Portfolio).ThenInclude(p => p.Assets).FirstOrDefault(u => u.Id == userId);
            if (user == null) throw new Exception("User not found");
            if (user.Portfolio == null) throw new Exception("Portfolio not found");
            var portfolio = user.Portfolio;
            var asset = await _dbContext.Assets.FirstOrDefaultAsync(a => a.PortfolioId == portfolio.Id && a.Symbol.Equals(trade.Symbol));

            if (asset == null || asset.Quantity < trade.Quantity) throw new InvalidOperationException("Not enough to sell");

            decimal price = await _cryptoService.GetCryptoPrice(trade.Symbol);
            decimal totalCost = price * (decimal)trade.Quantity;

            asset.Quantity -= trade.Quantity;
            if (asset.Quantity == 0)
            {
                _dbContext.Assets.Remove(asset);
            }
            var transaction = new Transaction
            {
                PortfolioId = portfolio.Id,
                Symbol = trade.Symbol,
                Quantity = trade.Quantity,
                Price = price,
                TimeStamp = DateTime.UtcNow,
            };

            await _dbContext.Transactions.AddAsync(transaction);

            portfolio.AvailableMoney += totalCost;
            await _dbContext.SaveChangesAsync();
        }

        public async Task<Dictionary<string, object>> GetPortfolio(string userId)
        {
            var user = _dbContext.Users.Include(u => u.Portfolio).ThenInclude(p => p.Assets).FirstOrDefault(u => u.Id == userId);
            if (user == null) throw new Exception("User not found");
            if (user.Portfolio == null) throw new Exception("Portfolio not found");
            var portfolio = user.Portfolio;
            var assets = new List<Dictionary<string, object>>();
            var totalValue = portfolio.AvailableMoney;

            var allTransactions = await _dbContext.Transactions
                .Where(t => t.PortfolioId == portfolio.Id)
                .ToListAsync();

            var transactionsBySymbol = allTransactions
                .GroupBy(t => t.Symbol)
                .ToDictionary(g => g.Key, g => g.ToList());

            var priceTasks = portfolio.Assets
                .ToDictionary(
                    asset => asset.Symbol,
                    asset => _cryptoService.GetCryptoPrice(asset.Symbol)
                );

            await Task.WhenAll(priceTasks.Values);

            foreach (var asset in portfolio.Assets)
            {
                var currentPrice = await priceTasks[asset.Symbol];
                var netQuantity = asset.Quantity;
                var assetValue = currentPrice * (decimal)netQuantity;
                totalValue += assetValue;

                transactionsBySymbol.TryGetValue(asset.Symbol, out var transactions);

                decimal netCost = transactions?.Sum(t => t.Price * (decimal)t.Quantity) ?? 0;

                assets.Add(new Dictionary<string, object>
        {
            { "symbol",  asset.Symbol },
            { "quantity", asset.Quantity },
            { "currentPrice", currentPrice },
            { "totalValue", assetValue },
            { "performanceAbs", assetValue - netCost },
            { "performanceRel", netCost != 0 ? (assetValue - netCost) / netCost * 100 : 0 },
        });
            }

            return new Dictionary<string, object>
    {
        { "totalAddedMoney", portfolio.TotalAddedMoney },
        { "avaibleMoney", portfolio.AvailableMoney },
        { "totalValue", totalValue },
        { "performanceAbs", totalValue - portfolio.TotalAddedMoney },
        { "performanceRel", portfolio.TotalAddedMoney != 0 ? (totalValue - portfolio.TotalAddedMoney) / portfolio.TotalAddedMoney * 100 : 0 },
        { "assets", assets }
    };
        }
    }
}
