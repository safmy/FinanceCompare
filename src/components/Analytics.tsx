import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { AnalyticsData } from '../types';
import './Analytics.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface AnalyticsProps {
  data: AnalyticsData | null;
}

const Analytics: React.FC<AnalyticsProps> = ({ data }) => {
  if (!data) return null;

  const categoryChartData = {
    labels: data.categorySummary.map(cat => cat.name),
    datasets: [{
      data: data.categorySummary.map(cat => cat.total),
      backgroundColor: [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF',
        '#FF9F40',
        '#FF6384',
        '#C9CBCF',
        '#4BC0C0',
        '#FF9F40',
      ],
    }],
  };

  const monthlyTrendData = {
    labels: data.monthlyTrends.map(trend => trend.month),
    datasets: [
      {
        label: 'Income',
        data: data.monthlyTrends.map(trend => trend.income),
        borderColor: '#4BC0C0',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
      },
      {
        label: 'Expenses',
        data: data.monthlyTrends.map(trend => trend.expenses),
        borderColor: '#FF6384',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1,
      },
      {
        label: 'Savings',
        data: data.monthlyTrends.map(trend => trend.savings),
        borderColor: '#36A2EB',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.1,
      },
    ],
  };

  const topMerchantsData = {
    labels: data.topMerchants.slice(0, 10).map(m => m.name),
    datasets: [{
      label: 'Total Spent',
      data: data.topMerchants.slice(0, 10).map(m => m.total),
      backgroundColor: '#FF6384',
    }],
  };

  return (
    <div className="analytics">
      <h2>Financial Analytics</h2>
      
      <div className="summary-cards">
        <div className="card income">
          <h3>Total Income</h3>
          <p className="amount">${data.totalIncome.toFixed(2)}</p>
        </div>
        <div className="card expenses">
          <h3>Total Expenses</h3>
          <p className="amount">${data.totalExpenses.toFixed(2)}</p>
        </div>
        <div className="card savings">
          <h3>Net Savings</h3>
          <p className="amount">${data.netSavings.toFixed(2)}</p>
          <p className="percentage">
            {((data.netSavings / data.totalIncome) * 100).toFixed(1)}% saved
          </p>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Spending by Category</h3>
          <div className="chart-wrapper">
            <Pie 
              data={categoryChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'right',
                  },
                },
              }}
            />
          </div>
        </div>

        <div className="chart-container">
          <h3>Monthly Trends</h3>
          <div className="chart-wrapper">
            <Line 
              data={monthlyTrendData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }}
            />
          </div>
        </div>

        <div className="chart-container wide">
          <h3>Top Merchants</h3>
          <div className="chart-wrapper">
            <Bar 
              data={topMerchantsData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }}
            />
          </div>
        </div>
      </div>

      <div className="category-breakdown">
        <h3>Category Breakdown</h3>
        <div className="category-list">
          {data.categorySummary.map(category => (
            <div key={category.name} className="category-item">
              <div className="category-info">
                <span className="name">{category.name}</span>
                <span className="count">{category.transactions.length} transactions</span>
              </div>
              <div className="category-amount">
                <span className="total">${category.total.toFixed(2)}</span>
                <span className="percentage">{category.percentage.toFixed(1)}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${category.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;