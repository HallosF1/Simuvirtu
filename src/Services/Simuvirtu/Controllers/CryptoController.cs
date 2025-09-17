using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Simuvirtu.Interfaces;

namespace Simuvirtu.Controllers
{
    [Authorize]
    [Route("api/[controller]")]
    [ApiController]
    public class CryptoController : ControllerBase
    {
        private readonly ICryptoService _cryptoService;

        public CryptoController(ICryptoService cryptoService) 
        {
            _cryptoService = cryptoService;
        }
        [HttpGet("{symbol}")]
        public async Task<ActionResult> GetPriceBySymbol(string symbol) 
        { 
            try
            {
                decimal price = await _cryptoService.GetCryptoPrice(symbol);
                return Ok(price);
            }
            catch (Exception ex)  
            {
                Console.WriteLine(ex.Message.ToString());
                return BadRequest(ex.Message);
            }
        }
    }
}
