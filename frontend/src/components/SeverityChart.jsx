import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

export default function SeverityChart({ counts, hasData }) {
  const data = {
    labels: ['Severe', 'Moderate', 'Mild'],
    datasets: [{
      data: [counts.severe, counts.moderate, counts.mild],
      backgroundColor: ['#DC2626', '#D97706', '#16A34A'],
      borderColor: ['#fff', '#fff', '#fff'],
      borderWidth: 2,
    }],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' },
    },
    cutout: '70%',
  }

  return (
    <div className="chart-body">
      {hasData ? (
        <div style={{ width: '100%', height: '240px' }}>
          <Doughnut data={data} options={options} />
        </div>
      ) : (
        <div className="empty-state">
          <p>Chart will appear here</p>
        </div>
      )}
    </div>
  )
}
