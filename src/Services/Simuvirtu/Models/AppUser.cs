using Microsoft.AspNetCore.Identity;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Simuvirtu.Models
{
    public class AppUser: IdentityUser
    {
        public Portfolio? Portfolio { get; set; }
    }
}
