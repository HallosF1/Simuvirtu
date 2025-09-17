using Simuvirtu.Models;

namespace Simuvirtu.Interfaces
{
    public interface ITokenService
    {
        string CreateToken(AppUser user);
    }
}
