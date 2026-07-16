"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  Download,
  Search,
  Eye,
  FileImage,
  FileSpreadsheet,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

interface Report {
  id: number;
  title: string;
  type: string;
  user: string;
  created_at: Date;
  status: string;
}

const mockReports: Report[] = [
  {
    id: 1,
    title: "Reporte mensual - Junio 2026",
    type: "pdf",
    user: "Admin",
    created_at: new Date(),
    status: "completed",
  },
  {
    id: 2,
    title: "Diagnósticos por enfermedad - Q2 2026",
    type: "excel",
    user: "Admin",
    created_at: new Date(Date.now() - 86400000 * 2),
    status: "completed",
  },
  {
    id: 3,
    title: "Rendimiento de modelos - Julio 2026",
    type: "pdf",
    user: "Admin",
    created_at: new Date(Date.now() - 86400000 * 5),
    status: "completed",
  },
  {
    id: 4,
    title: "Análisis de tendencias - Julio 2026",
    type: "image",
    user: "Admin",
    created_at: new Date(Date.now() - 86400000 * 7),
    status: "completed",
  },
  {
    id: 5,
    title: "Reporte semanal de diagnósticos",
    type: "pdf",
    user: "Admin",
    created_at: new Date(Date.now() - 86400000 * 10),
    status: "generating",
  },
];

const typeIcon = {
  pdf: FileText,
  excel: FileSpreadsheet,
  image: FileImage,
};

export default function ReportsPage() {
  const [search, setSearch] = useState("");

  const filtered = mockReports.filter((r) =>
    r.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reportes</h2>
        <p className="text-muted-foreground">
          Visualiza y descarga reportes generados automáticamente
        </p>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar reportes..."
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Reportes Disponibles</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Título</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Usuario</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((report) => {
                const Icon = typeIcon[report.type as keyof typeof typeIcon] || FileText;
                return (
                  <TableRow key={report.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        {report.title}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="uppercase">
                        {report.type}
                      </Badge>
                    </TableCell>
                    <TableCell>{report.user}</TableCell>
                    <TableCell>{formatDate(report.created_at)}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          report.status === "completed"
                            ? "success"
                            : "warning"
                        }
                      >
                        {report.status === "completed"
                          ? "Completado"
                          : "Generando"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="icon">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={report.status !== "completed"}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
