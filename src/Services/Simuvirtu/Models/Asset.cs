using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Simuvirtu.Models
{
    public class Asset
    {
        public int Id { get; set; }
        [ForeignKey("Portfolio")]
        public int PortfolioId { get; set; }
        public Portfolio Portfolio { get; set; }
        [Required]
        public string Symbol { get; set; }
        public float Quantity { get; set; }
        
    }
}
