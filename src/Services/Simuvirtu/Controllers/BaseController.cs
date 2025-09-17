using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Simuvirtu.Data;
using Simuvirtu.Models;

namespace Simuvirtu.Controllers
{
    [ApiController]
    public class BaseController<T> : ControllerBase
    {
        protected readonly ILogger<T> _logger;
        protected readonly UserManager<AppUser> _userManager;
        protected readonly ApplicationDbContext _dbContext;
        public BaseController(UserManager<AppUser> userManager, ApplicationDbContext dbContext, ILogger<T> logger)
        {
            _logger = logger;
            _userManager = userManager;
            _dbContext = dbContext;
        }
    }
}
