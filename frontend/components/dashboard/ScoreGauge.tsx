"use client";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface Props {
  score: number;
  riskLevel: string;
}

const riskColors = {
  VERT: "#16a34a",
  ORANGE: "#d97706",
  ROUGE: "#dc2626",
};

export default function ScoreGauge({ score, riskLevel }: Props) {
  const color = riskColors[riskLevel as keyof typeof riskColors] || "#64748b";
  const data = [{ value: score, fill: color }];

  return (
    <div className="relative flex flex-col items-center">
      <RadialBarChart
        width={160}
        height={160}
        cx={80}
        cy={80}
        innerRadius={55}
        outerRadius={75}
        barSize={14}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar
          background={{ fill: "#f1f5f9" }}
          dataKey="value"
          cornerRadius={8}
          angleAxisId={0}
        />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="text-xs text-gray-500 font-medium">/100</span>
      </div>
    </div>
  );
}
