using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using Simuvirtu.Models;

namespace Simuvirtu.Data
{
    public class ApplicationDbContext: IdentityDbContext<AppUser>
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options): base(options)
        {
            
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<AppUser>()
                .HasIndex(u => u.Email)
                .IsUnique();

            modelBuilder.Entity<AppUser>()
                .HasOne(u => u.Portfolio)
                .WithOne(p => p.User)
                .HasForeignKey<Portfolio>(p => p.UserId);

            modelBuilder.Entity<Portfolio>()
                .HasMany(p => p.Assets)
                .WithOne(a => a.Portfolio)
                .HasForeignKey(a => a.PortfolioId);

            modelBuilder.Entity<Portfolio>()
                .HasMany(p => p.Transactions)
                .WithOne(t => t.Portfolio)
                .HasForeignKey(t => t.PortfolioId);

            List<IdentityRole> roles = new List<IdentityRole>()
            {
                new IdentityRole() 
                {
                    Id = "1",
                    Name = "Admin",
                    NormalizedName = "ADMIN"
                },
                new IdentityRole()
                {
                    Id = "2",
                    Name = "User",
                    NormalizedName = "USER"
                }
            };
            modelBuilder.Entity<IdentityRole>().HasData(roles);
        }

        public DbSet<AppUser> AppUsers { get; set; }
        public DbSet<Portfolio> Portfolios { get; set; }
        public DbSet<Transaction> Transactions { get; set; }
        public DbSet<Asset> Assets { get; set; }
    }
}
