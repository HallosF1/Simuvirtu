using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Rewrite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration.UserSecrets;
using Simuvirtu.Data;
using Simuvirtu.Dtos;
using Simuvirtu.DTOs;
using Simuvirtu.Interfaces;
using Simuvirtu.Models;

namespace Simuvirtu.Controllers
{
    [Route("api/account")]
    [ApiController]
    public class AccountController : BaseController<AccountController>
    {
        private readonly ITokenService _tokenService;
        private readonly SignInManager<AppUser> _signInManager;
        public AccountController(UserManager<AppUser> userManager, SignInManager<AppUser> signInManager, IUnitOfWork uow, ILogger<AccountController> logger, ITokenService tokenService) : base(userManager, uow, logger)
        {
            _tokenService = tokenService;
            _signInManager = signInManager;
        }

        [HttpPost("register")]
        public async Task<IActionResult> Register([FromBody] UserCreate userCreate, CancellationToken ct = default)
        {
            await using var tx = await _uow.BeginTransactionAsync(ct);
            try
            {
                if (!ModelState.IsValid) return BadRequest(ModelState);
                var appUser = new AppUser()
                {
                    Email = userCreate.Email,
                    UserName = userCreate.Username,
                };
                var createdUser = await _userManager.CreateAsync(appUser, userCreate.Password);
                if (createdUser.Succeeded)
                {
                    var roleResult = await _userManager.AddToRoleAsync(appUser, "User");
                    var portfolio = new Portfolio
                    {
                        UserId = appUser.Id,
                        User = appUser,
                        TotalAddedMoney = 0,
                        AvailableMoney = 0
                    };
                    _uow.SaveChangesAsync(ct).Wait();
                    await _uow.CommitAsync(tx, ct);
                    if (roleResult.Succeeded)
                    {
                        return Ok(new NewUserDto
                        {
                            UserName = appUser.UserName,
                            Email = appUser.Email,
                            Token = _tokenService.CreateToken(appUser)
                        });
                    }
                    else
                    {
                        return BadRequest(roleResult.Errors);
                    }
                }
                else 
                {
                    return BadRequest(createdUser.Errors);
                }
            }
            catch (Exception ex) 
            { 
                return BadRequest($"Failed to register {ex.Message}");
            }
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login(LoginDto loginDto) 
        {
            if (!ModelState.IsValid) 
                return BadRequest(ModelState);

            var user = await _userManager.Users.FirstOrDefaultAsync(x => x.UserName == loginDto.UserName.ToLower());
            if (user == null) return Unauthorized("Invalid Username");
            var result = await _signInManager.CheckPasswordSignInAsync(user, loginDto.Password, false);
            if (!result.Succeeded) return Unauthorized("Username not found and/or password incorrect");
            return Ok(new NewUserDto
            {
                UserName = loginDto.UserName,
                Email = user.Email,
                Token= _tokenService.CreateToken(user)
            });
        }
    }
}
