using System.ComponentModel.DataAnnotations;

namespace Simuvirtu.DTOs
{
    public class UserCreate
    {
        [Required]
        public string Username { get; set; }
        [Required]
        [EmailAddress]
        public string Email { get; set; }
        [Required]
        public string Password { get; set; }
    }
}
