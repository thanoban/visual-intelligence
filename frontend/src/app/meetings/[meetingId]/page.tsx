import { MeetingDetailClient } from "@/components/meeting-detail-client";

export default async function MeetingDetailPage({
  params,
}: {
  params: Promise<{ meetingId: string }>;
}) {
  const { meetingId } = await params;
  return <MeetingDetailClient meetingId={meetingId} />;
}
