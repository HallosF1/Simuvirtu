using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Simuvirtu.Data;
using Simuvirtu.DTOs;
using Simuvirtu.Interfaces;
using Simuvirtu.Models;
using System.Security.Claims;

namespace Simuvirtu.Controllers
{
    [Authorize]
    [Route("api/[controller]")]
    [ApiController]
    public class PortfolioController : BaseController<PortfolioController>
    {
        private readonly IPortfolioService _portfolioService;

        public PortfolioController(UserManager<AppUser> userManager, ApplicationDbContext dbContext, ILogger<PortfolioController> logger, IPortfolioService portfolioService) : base(userManager, dbContext, logger)
        {
            _portfolioService = portfolioService;
        }

        [HttpPost("/addmoney")]
        public async Task<IActionResult> AddMoney([FromBody] AddMoney money)
        {
            try
            {
                var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (userId == null) return Unauthorized();

                await _portfolioService.AddMoney(userId, money);
                return Ok("Money Added Successfully");
            }
            catch (Exception ex)
            {
                return BadRequest(ex.Message);
            }
        }

        [HttpPost("/buyasset")]
        public async Task<IActionResult> BuyAsset([FromBody] TradeAsset trade)
        {
            try
            {
                var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (userId == null) return Unauthorized();
                await _portfolioService.BuyAsset(userId, trade);
                return Ok("Asset Successfully Bought");
            }
            catch (Exception ex)
            {
                return BadRequest(ex.Message);
            }
        }

        [HttpPost("/sellasset")]
        public async Task<IActionResult> SellAsset([FromBody] TradeAsset trade)
        {
            try
            {
                var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (userId == null) return Unauthorized();
                await _portfolioService.SellAsset(userId, trade);
                return Ok("Asset Successfully Selled");
            }
            catch (Exception ex)
            {
                return BadRequest(ex.Message);
            }
        }

        [HttpGet("me")]
        public async Task<IActionResult> GetPortfolio()
        {
            try
            {
                var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (userId == null) return Unauthorized();
                var portfolio = await _portfolioService.GetPortfolio(userId);
                return Ok(portfolio);
            }
            catch (Exception ex)
            {
                return BadRequest(ex.Message);
            }
        }
    }
}
