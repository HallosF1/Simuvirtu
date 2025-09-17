using System.ComponentModel.DataAnnotations.Schema;

namespace Simuvirtu.Models
{
    public class Portfolio
    {
        public int Id { get; set; }
        [ForeignKey("AppUser")]
        public string UserId { get; set; }
        public AppUser User { get; set; }
        public decimal TotalAddedMoney { get; set; } = 0;
        public decimal AvailableMoney { get; set; } = 0;
        public ICollection<Asset> Assets { get; set; } = new List<Asset>();
        public ICollection<Transaction> Transactions { get; set; } = new List<Transaction>();
    }
}
